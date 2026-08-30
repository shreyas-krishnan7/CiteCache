
from __future__ import annotations

import json
import time
from pathlib import Path

from app.config import settings
from app.ingestion.vector_store import get_client
from app.retrieval.bm25_index import build_bm25_index
from app.cache.semantic_cache import cache_clear
from app.graph.build_graph import build_graph
from app.eval.golden_set import GOLDEN_SET
from app.eval.metrics import score_question, aggregate

REPORT_PATH = "data/eval_report.json"


def main() -> None:
    if settings.llm_provider == "openai" and not settings.openai_api_key:
        raise SystemExit("LLM_PROVIDER=openai but OPENAI_API_KEY is not set in .env")
    if settings.llm_provider == "anthropic" and not settings.anthropic_api_key:
        raise SystemExit("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set in .env")
    if settings.llm_provider == "groq" and not settings.groq_api_key:
        raise SystemExit("LLM_PROVIDER=groq but GROQ_API_KEY is not set in .env")
    if settings.llm_provider == "gemini" and not settings.gemini_api_key:
        raise SystemExit("LLM_PROVIDER=gemini but GEMINI_API_KEY is not set in .env")

    client = get_client()
    print("Clearing cache so every question is freshly generated...")
    cache_clear(client)

    print("Building BM25 index...")
    bm25 = build_bm25_index(client, settings.doc_collection)
    graph = build_graph()

    results = []
    print(f"\nRunning {len(GOLDEN_SET)} golden questions "
          f"(now with LLM-judge answer grading -- one extra call per answerable question)...\n")
    for gq in GOLDEN_SET:
        start = time.perf_counter()
        state = graph.invoke({
            "query": gq.question, "client": client, "bm25_index": bm25,
            "collection": settings.doc_collection, "start_time": start,
        })
        latency_ms = (time.perf_counter() - start) * 1000
        result = score_question(gq, state, latency_ms)
        results.append(result)

        status_bits = []
        if result.retrieval_hit is not None:
            status_bits.append("retrieval:OK" if result.retrieval_hit else "retrieval:MISS")
        if result.answer_correct_keyword is not None:
            status_bits.append("keyword:OK" if result.answer_correct_keyword else "keyword:WRONG")
        if result.llm_judge_correct is not None:
            status_bits.append("judge:OK" if result.llm_judge_correct else "judge:WRONG")
        status_bits.append("insuff_ctx:OK" if result.insufficient_context_correct else "insuff_ctx:WRONG")
        print(f"  [{gq.id}] {' '.join(status_bits):<58} conf={result.confidence:.2f}  {gq.question!r}")

    summary = aggregate(results)

    print(f"\n{'='*70}")
    print("EVAL SUMMARY")
    print(f"{'='*70}")
    print(f"  Total questions:                    {summary['total_questions']} "
          f"({summary['answerable_questions']} answerable, {summary['unanswerable_questions']} out-of-corpus)")
    if summary["retrieval_accuracy"] is not None:
        print(f"  Retrieval accuracy:                  {summary['retrieval_accuracy']*100:.1f}%")
    if summary["answer_accuracy_keyword_based"] is not None:
        print(f"  Answer accuracy (keyword-based):      {summary['answer_accuracy_keyword_based']*100:.1f}%")
    if summary["answer_accuracy_llm_judge"] is not None:
        print(f"  Answer accuracy (LLM-judge):           {summary['answer_accuracy_llm_judge']*100:.1f}%")
    if summary["false_insufficient_context_rate"] is not None:
        print(f"  False 'insufficient_context' rate:    {summary['false_insufficient_context_rate']*100:.1f}%")
    if summary["hallucination_rate"] is not None:
        print(f"  Hallucination rate:                   {summary['hallucination_rate']*100:.1f}%")
    print(f"  Avg citation support rate:           {summary['avg_citation_support_rate']*100:.1f}%")
    if summary["avg_confidence_answerable"] is not None:
        print(f"  Avg confidence (answerable):         {summary['avg_confidence_answerable']:.3f}")
    if summary["avg_confidence_unanswerable"] is not None:
        print(f"  Avg confidence (out-of-corpus):      {summary['avg_confidence_unanswerable']:.3f}")
    print(f"  Avg latency:                          {summary['avg_latency_ms']:.0f}ms")

    report = {
        "summary": summary,
        "per_question": [
            {
                "id": r.id, "question": r.question, "should_be_answerable": r.should_be_answerable,
                "expected_source": r.expected_source, "retrieved_sources": r.retrieved_sources,
                "retrieval_hit": r.retrieval_hit, "answer": r.answer,
                "reference_answer": r.reference_answer,
                "insufficient_context": r.insufficient_context,
                "insufficient_context_correct": r.insufficient_context_correct,
                "keyword_coverage": r.keyword_coverage, "answer_correct_keyword": r.answer_correct_keyword,
                "llm_judge_correct": r.llm_judge_correct, "llm_judge_reasoning": r.llm_judge_reasoning,
                "citation_support_rate": r.citation_support_rate, "confidence": r.confidence,
                "latency_ms": r.latency_ms,
            }
            for r in results
        ],
    }
    Path(REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(REPORT_PATH).write_text(json.dumps(report, indent=2))
    print(f"\nFull report written to {REPORT_PATH}")
    print("\nWatch for cases where keyword:WRONG but judge:OK -- those are answers that were")
    print("actually correct but phrased differently than the keyword list expected.")


if __name__ == "__main__":
    main()
