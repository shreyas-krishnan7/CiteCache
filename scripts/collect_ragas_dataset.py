"""
Stage A of RAGAS evaluation -- runs in your MAIN citecache venv.

Runs each answerable golden-set question through the REAL, compiled
LangGraph pipeline (same as run_eval.py), and saves the question,
generated answer, retrieved chunk texts (contexts), and hand-written
reference answer to a JSON file. This is the exact shape RAGAS needs:
{question, answer, contexts, ground_truth}.

This stage uses your existing Gemini-backed pipeline, which already
has retry-with-backoff for rate limits -- no new throttling needed
here, but a small inter-question pacing delay and checkpointing are
added anyway for consistency with Stage B and so this is safe to
interrupt and resume (or trigger repeatedly via Task Scheduler).

Stage B (a SEPARATE venv, see ragas_eval/) reads the JSON file this
script produces and computes RAGAS metrics against it -- kept
separate specifically because ragas needs an older langchain-core
than this project's langgraph installation can tolerate; the two
cannot coexist in one Python environment. This JSON file is the
handoff point between them.

Usage:
    python -m scripts.collect_ragas_dataset
    python -m scripts.collect_ragas_dataset --corpus labour
    (safe to re-run -- resumes from the dataset file if it already has
    some questions collected)
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from app.config import settings
from app.ingestion.vector_store import get_client
from app.retrieval.bm25_index import build_bm25_index
from app.cache.semantic_cache import cache_clear
from app.graph.build_graph import build_graph
from app.generation.prompts import chunk_provenance

# Each corpus has its own golden set and its own dataset file, so
# switching corpora doesn't overwrite the other one's collected answers.
CORPORA = {
    "support": ("app.eval.golden_set", "data/ragas_dataset.json"),
    "labour": ("app.eval.golden_set_labour", "data/ragas_dataset_labour.json"),
}
INTER_QUESTION_DELAY_SECONDS = 4  # light pacing; existing retry/backoff handles the rest


def _load_existing(dataset_path: str) -> dict:
    path = Path(dataset_path)
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save(dataset_path: str, results: dict) -> None:
    Path(dataset_path).parent.mkdir(parents=True, exist_ok=True)
    Path(dataset_path).write_text(json.dumps(results, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", choices=sorted(CORPORA), default="support")
    args = parser.parse_args()

    module_name, dataset_path = CORPORA[args.corpus]
    golden_set = __import__(module_name, fromlist=["GOLDEN_SET"]).GOLDEN_SET

    if settings.llm_provider == "gemini" and not settings.gemini_api_key:
        raise SystemExit("LLM_PROVIDER=gemini but GEMINI_API_KEY is not set in .env")

    # Only questions with a reference_answer are usable for RAGAS's
    # standard metrics (which compare against ground truth) -- the
    # 5 deliberately out-of-corpus questions are skipped here.
    questions = [gq for gq in golden_set if gq.should_be_answerable and gq.reference_answer]

    results = _load_existing(dataset_path)
    remaining = [gq for gq in questions if gq.id not in results]

    if not remaining:
        print(f"All {len(questions)} questions already collected in {dataset_path}. Nothing to do.")
        print("Delete that file (or a specific question's entry) to re-collect.")
        return

    print(f"{len(results)} already collected, {len(remaining)} remaining.")

    client = get_client()
    print("Building BM25 index...")
    bm25 = build_bm25_index(client, settings.doc_collection)
    graph = build_graph()
    failed: list[str] = []

    for i, gq in enumerate(remaining, start=1):
        print(f"  [{i}/{len(remaining)}] {gq.id}: {gq.question!r}")
        # Cleared before EVERY question, not once per run: a cache hit is served
        # by serve_cached_node, which never populates `chunks`, so it would record
        # an entry with empty contexts and RAGAS would score it near zero for a
        # reason that has nothing to do with retrieval quality. Questions cached
        # earlier in this same run are close enough to trigger that.
        cache_clear(client)
        try:
            state = graph.invoke({
                "query": gq.question,
                "client": client,
                "bm25_index": bm25,
                "collection": settings.doc_collection,
                "start_time": time.perf_counter(),
            })
        except Exception as e:
            # Left unrecorded, so the next invocation retries it; one bad question
            # must not stop the rest of the run.
            print(f"    FAILED: {type(e).__name__}: {str(e)[:300]}")
            failed.append(gq.id)
            continue

        chunks = state.get("chunks") or []
        # Record each context exactly as the generator saw it, label included:
        # the judge scores the answer against these, and the answer names
        # documents/sections because the label showed them.
        contexts = [
            f"[{chunk_provenance(c)}]\n{c.text}" if chunk_provenance(c) else c.text
            for c in chunks
        ]
        answer = state.get("final_answer", "")

        results[gq.id] = {
            "question": gq.question,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": gq.reference_answer,
        }
        _save(dataset_path, results)  # checkpoint after every question, not just at the end

        if i < len(remaining):
            time.sleep(INTER_QUESTION_DELAY_SECONDS)

    print(f"\nDone. {len(results)} questions collected in {dataset_path}.")
    if failed:
        raise SystemExit(f"{len(failed)} question(s) failed and were not recorded: {failed}. "
                         f"Re-run this script to retry just those.")
    print("Next: switch to the ragas_eval/ virtual environment and run its script.")


if __name__ == "__main__":
    main()
