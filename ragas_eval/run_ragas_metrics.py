"""
Stage B of RAGAS evaluation -- runs in the SEPARATE `ragas_eval` venv,
NOT your main citecache venv.

Reads data/ragas_dataset.json (produced by Stage A --
scripts/collect_ragas_dataset.py in your main venv) and computes
RAGAS metrics against it, using Gemini as the judge LLM and a local
HuggingFace model for embeddings.

Rate-limit strategy, tuned for Gemini's 15 requests/min free tier:
  - RunConfig(max_workers=1): every LLM call is fully serialized.
  - One question processed per evaluate() call.
  - A fixed delay between questions (default 45s).
  - Every result written to disk immediately -- safe to interrupt or
    schedule in chunks via Windows Task Scheduler.

Usage:
    python run_ragas_metrics.py
    python run_ragas_metrics.py --batch-size 5
    python run_ragas_metrics.py --corpus labour
    python run_ragas_metrics.py --corpus labour --judge groq --ids b01,w05,o10
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path

from dotenv import load_dotenv

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent
load_dotenv(_THIS_DIR / ".env")
load_dotenv(_PROJECT_ROOT / ".env")  # GROQ_API_KEY lives here; never overrides ragas_eval/.env

CORPORA = {
    "support": ("ragas_dataset.json", "ragas_report.json"),
    "labour": ("ragas_dataset_labour.json", "ragas_report_labour.json"),
}
INTER_QUESTION_DELAY_SECONDS = float(os.getenv("RAGAS_INTER_QUESTION_DELAY_SECONDS", "45"))
GEMINI_MODEL = os.getenv("RAGAS_GEMINI_MODEL", "gemini-3.5-flash-lite")
GROQ_MODEL = os.getenv("RAGAS_GROQ_MODEL", "openai/gpt-oss-120b")
LOCAL_EMBEDDING_MODEL = os.getenv("RAGAS_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
METRICS = ["faithfulness", "response_relevancy", "context_recall", "factual_correctness"]


def _load_dataset(dataset_path: Path) -> dict:
    if not dataset_path.exists():
        raise SystemExit(
            f"{dataset_path} not found. Run scripts/collect_ragas_dataset.py "
            f"in your MAIN citecache venv first."
        )
    return json.loads(dataset_path.read_text())


def _load_report(report_path: Path) -> dict:
    if report_path.exists():
        return json.loads(report_path.read_text())
    return {}


def _save_report(report_path: Path, report: dict) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2))


def _judge_name(judge: str) -> str:
    return f"gemini:{GEMINI_MODEL}" if judge == "gemini" else f"groq:{GROQ_MODEL}"


def _build_evaluator(judge: str = "gemini"):
    from langchain_huggingface import HuggingFaceEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    if judge == "groq":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise SystemExit("GROQ_API_KEY is not set in ragas_eval/.env or the project .env")
        llm = ChatOpenAI(model=GROQ_MODEL, api_key=api_key, base_url="https://api.groq.com/openai/v1", temperature=0)
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise SystemExit("GEMINI_API_KEY is not set in ragas_eval/.env")
        llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=api_key, temperature=0)

    embeddings = HuggingFaceEmbeddings(model_name=LOCAL_EMBEDDING_MODEL)
    return LangchainLLMWrapper(llm), LangchainEmbeddingsWrapper(embeddings)


def _find_key(scores: dict, prefix: str):
    """
    RAGAS's result columns don't always match the metric's plain name --
    e.g. FactualCorrectness returns a column literally named
    'factual_correctness(mode=f1)', not 'factual_correctness'. Doing an
    exact-key lookup for the plain name silently returns None every
    time, which is exactly the bug that caused factual_correctness to
    show up as null for all 24 questions in the first real run -- the
    metric was computing fine, the extraction code just never found it.
    This searches for any column whose name STARTS WITH the expected
    prefix, so it's robust to the mode suffix (or any other RAGAS
    version formatting its column names differently).
    """
    for key, value in scores.items():
        if key == prefix or key.startswith(prefix + "("):
            return value
    return None


def _score_one_question(entry: dict, evaluator_llm, evaluator_embeddings) -> dict:
    from ragas import EvaluationDataset, SingleTurnSample, evaluate
    from ragas.metrics import Faithfulness, ResponseRelevancy, LLMContextRecall, FactualCorrectness
    from ragas.run_config import RunConfig

    sample = SingleTurnSample(
        user_input=entry["question"],
        response=entry["answer"],
        retrieved_contexts=entry["contexts"] or ["(no context retrieved)"],
        reference=entry["ground_truth"],
    )
    dataset = EvaluationDataset(samples=[sample])

    run_config = RunConfig(max_workers=1, timeout=180, max_retries=8, max_wait=60)
    metrics = [Faithfulness(), ResponseRelevancy(), LLMContextRecall(), FactualCorrectness()]

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        run_config=run_config,
        raise_exceptions=False,
    )

    scores = result.to_pandas().iloc[0].to_dict()
    return {
        "question": entry["question"],
        "faithfulness": _find_key(scores, "faithfulness"),
        "response_relevancy": _find_key(scores, "answer_relevancy") or _find_key(scores, "response_relevancy"),
        "context_recall": _find_key(scores, "context_recall"),
        "factual_correctness": _find_key(scores, "factual_correctness"),  # <-- the fix
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--corpus", choices=sorted(CORPORA), default="support")
    parser.add_argument("--judge", choices=["gemini", "groq"], default="gemini",
                        help="Judge LLM. Each judge writes its own report file.")
    parser.add_argument("--ids", default=None, help="Comma-separated question ids to score (default: all).")
    args = parser.parse_args()

    dataset_name, report_name = CORPORA[args.corpus]
    if args.judge != "gemini":
        report_name = report_name.replace(".json", f"_{args.judge}.json")
    dataset_path = _PROJECT_ROOT / "data" / dataset_name
    report_path = _PROJECT_ROOT / "data" / report_name
    judge = _judge_name(args.judge)

    dataset = _load_dataset(dataset_path)
    report = _load_report(report_path)

    # An average over questions scored by different judges is meaningless, and a
    # resume after a judge/model change would silently produce exactly that.
    foreign = {r.get("judge", "<unrecorded>") for r in report.values()} - {judge}
    if foreign:
        raise SystemExit(f"{report_path.name} already holds scores from {sorted(foreign)}, not {judge}. "
                         f"Move that report aside before scoring with a different judge.")

    wanted = list(dataset)
    if args.ids:
        wanted = [q.strip() for q in args.ids.split(",") if q.strip()]
        unknown = [q for q in wanted if q not in dataset]
        if unknown:
            raise SystemExit(f"Unknown question id(s) for this dataset: {unknown}")

    remaining_ids = [qid for qid in wanted if qid not in report]
    if not remaining_ids:
        print(f"All {len(wanted)} requested questions already scored in {report_path}. Nothing to do.")
        _print_summary(report)
        return

    to_process = remaining_ids[: args.batch_size] if args.batch_size else remaining_ids
    print(f"Judge: {judge}. {len(report)} already scored, {len(remaining_ids)} remaining, "
          f"processing {len(to_process)} this run (delay={INTER_QUESTION_DELAY_SECONDS}s between questions).")

    evaluator_llm, evaluator_embeddings = _build_evaluator(args.judge)

    for i, qid in enumerate(to_process, start=1):
        print(f"  [{i}/{len(to_process)}] scoring {qid}...")
        try:
            scores = _score_one_question(dataset[qid], evaluator_llm, evaluator_embeddings)
            # RAGAS swallows judge failures (raise_exceptions=False) and hands back
            # NaN, which looks like a successful result. Persisting it poisons the
            # report permanently: the id is now present, so every resume skips it.
            # A quota cut-off mid-question leaves only SOME metrics NaN, so any NaN
            # disqualifies the whole entry -- it is retried rather than half-scored.
            nan_metrics = [m for m in METRICS if isinstance(scores[m], float) and math.isnan(scores[m])]
            if nan_metrics:
                print(f"    NaN for {nan_metrics} (judge call failed -- likely quota) "
                      f"-- not recorded, will retry on next invocation.")
            else:
                scores["judge"] = judge
                report[qid] = scores
                _save_report(report_path, report)
                print(f"    faithfulness={scores['faithfulness']}  "
                      f"relevancy={scores['response_relevancy']}  "
                      f"context_recall={scores['context_recall']}  "
                      f"factual_correctness={scores['factual_correctness']}")
        except Exception as e:
            print(f"    FAILED: {e}  -- will retry on next invocation.")

        if i < len(to_process):
            time.sleep(INTER_QUESTION_DELAY_SECONDS)

    remaining_after = len([qid for qid in wanted if qid not in report])
    recorded = len(to_process) - len([q for q in to_process if q not in report])
    print(f"\nThis run recorded {recorded} of {len(to_process)} question(s). {remaining_after} still remaining.")
    if remaining_after == 0:
        _print_summary(report)


def _print_summary(report: dict) -> None:
    import math
    import statistics
    judges = sorted({r.get("judge", "<unrecorded>") for r in report.values()})
    print(f"\n{'='*60}\nRAGAS SUMMARY ({len(report)} questions, judge: {', '.join(judges)})\n{'='*60}")
    for m in METRICS:
        # RAGAS yields NaN -- not None -- for a metric it could not compute, which
        # it does when the answer is a refusal and there are no statements to
        # verify. NaN is not None, so filtering only on None lets a single
        # unscorable question turn the whole mean into nan.
        values = [
            r[m] for r in report.values()
            if isinstance(r.get(m), (int, float)) and not math.isnan(r[m])
        ]
        if values:
            skipped = len(report) - len(values)
            note = f", {skipped} unscorable" if skipped else ""
            print(f"  {m}: {statistics.mean(values):.3f}  (n={len(values)}{note})")
        else:
            print(f"  {m}: no valid scores (n=0)")


if __name__ == "__main__":
    main()
