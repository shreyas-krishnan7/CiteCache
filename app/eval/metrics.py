"""
Scoring for the golden-set eval.

Now computes TWO independent answer-correctness signals per question:
  - keyword_coverage / answer_correct_keyword: the original fast,
    free, zero-latency substring check.
  - llm_judge_correct / llm_judge_reasoning: semantic grading via
    app/eval/llm_judge.py, costs one LLM call per answerable
    question, catches cases the keyword check misses (e.g. correct
    answers phrased differently than the expected literal keywords).

Both are reported in aggregate() so you can see exactly how much the
keyword check was under/over-counting failures, rather than silently
replacing one blunt instrument with a black-box one.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.eval.golden_set import GoldenQuestion
from app.eval.llm_judge import judge_answer


@dataclass
class QuestionResult:
    id: str
    question: str
    should_be_answerable: bool
    expected_source: str | None
    expected_keywords: list[str]
    reference_answer: str | None

    answer: str
    insufficient_context: bool
    retrieved_sources: list[str]
    citation_support_rate: float
    confidence: float
    latency_ms: float

    retrieval_hit: bool | None
    insufficient_context_correct: bool

    keyword_coverage: float | None
    answer_correct_keyword: bool | None

    llm_judge_correct: bool | None
    llm_judge_reasoning: str | None


def score_question(
    gq: GoldenQuestion,
    state: dict,
    latency_ms: float,
    keyword_threshold: float = 0.5,
    run_llm_judge: bool = True,
) -> QuestionResult:
    generated = state.get("generated")
    chunks = state.get("chunks") or []
    confidence_obj = state.get("confidence")

    answer = state.get("final_answer", "")
    insufficient = generated.insufficient_context if generated else False
    retrieved_sources = [c.source for c in chunks]

    retrieval_hit = None
    if gq.expected_source is not None:
        retrieval_hit = gq.expected_source in retrieved_sources

    expected_insufficient = not gq.should_be_answerable
    insufficient_context_correct = insufficient == expected_insufficient

    keyword_coverage = None
    answer_correct_keyword = None
    if gq.should_be_answerable and gq.expected_keywords:
        lower_answer = answer.lower()
        found = sum(1 for kw in gq.expected_keywords if kw.lower() in lower_answer)
        keyword_coverage = found / len(gq.expected_keywords)
        answer_correct_keyword = keyword_coverage >= keyword_threshold

    llm_judge_correct = None
    llm_judge_reasoning = None
    if run_llm_judge and gq.should_be_answerable and gq.reference_answer and not insufficient:
        verdict = judge_answer(gq.question, gq.reference_answer, answer)
        llm_judge_correct = verdict.correct
        llm_judge_reasoning = verdict.reasoning
    elif run_llm_judge and gq.should_be_answerable and gq.reference_answer and insufficient:
        # Model declined to answer a question that should have been answerable --
        # that's a correctness failure by definition, no need to spend an LLM call grading it.
        llm_judge_correct = False
        llm_judge_reasoning = "Model returned insufficient_context on a question that should be answerable."

    citation_support_rate = confidence_obj.citation_support_rate if confidence_obj else 0.0
    confidence = confidence_obj.confidence if confidence_obj else 0.0

    return QuestionResult(
        id=gq.id,
        question=gq.question,
        should_be_answerable=gq.should_be_answerable,
        expected_source=gq.expected_source,
        expected_keywords=gq.expected_keywords,
        reference_answer=gq.reference_answer,
        answer=answer,
        insufficient_context=insufficient,
        retrieved_sources=retrieved_sources,
        citation_support_rate=citation_support_rate,
        confidence=confidence,
        latency_ms=latency_ms,
        retrieval_hit=retrieval_hit,
        insufficient_context_correct=insufficient_context_correct,
        keyword_coverage=keyword_coverage,
        answer_correct_keyword=answer_correct_keyword,
        llm_judge_correct=llm_judge_correct,
        llm_judge_reasoning=llm_judge_reasoning,
    )


def aggregate(results: list[QuestionResult]) -> dict:
    answerable = [r for r in results if r.should_be_answerable]
    unanswerable = [r for r in results if not r.should_be_answerable]

    retrieval_hits = [r.retrieval_hit for r in answerable if r.retrieval_hit is not None]
    retrieval_accuracy = sum(retrieval_hits) / len(retrieval_hits) if retrieval_hits else None

    keyword_flags = [r.answer_correct_keyword for r in answerable if r.answer_correct_keyword is not None]
    answer_accuracy_keyword = sum(keyword_flags) / len(keyword_flags) if keyword_flags else None

    judge_flags = [r.llm_judge_correct for r in answerable if r.llm_judge_correct is not None]
    answer_accuracy_llm_judge = sum(judge_flags) / len(judge_flags) if judge_flags else None

    ic_correct_answerable = [r.insufficient_context_correct for r in answerable]
    false_insufficient_rate = (
        1 - (sum(ic_correct_answerable) / len(ic_correct_answerable)) if ic_correct_answerable else None
    )

    ic_correct_unanswerable = [r.insufficient_context_correct for r in unanswerable]
    hallucination_rate = (
        1 - (sum(ic_correct_unanswerable) / len(ic_correct_unanswerable)) if ic_correct_unanswerable else None
    )

    avg_citation_support = sum(r.citation_support_rate for r in results) / len(results) if results else 0.0
    avg_confidence_answerable = sum(r.confidence for r in answerable) / len(answerable) if answerable else None
    avg_confidence_unanswerable = sum(r.confidence for r in unanswerable) / len(unanswerable) if unanswerable else None
    avg_latency = sum(r.latency_ms for r in results) / len(results) if results else 0.0

    return {
        "total_questions": len(results),
        "answerable_questions": len(answerable),
        "unanswerable_questions": len(unanswerable),
        "retrieval_accuracy": retrieval_accuracy,
        "answer_accuracy_keyword_based": answer_accuracy_keyword,
        "answer_accuracy_llm_judge": answer_accuracy_llm_judge,
        "false_insufficient_context_rate": false_insufficient_rate,
        "hallucination_rate": hallucination_rate,
        "avg_citation_support_rate": avg_citation_support,
        "avg_confidence_answerable": avg_confidence_answerable,
        "avg_confidence_unanswerable": avg_confidence_unanswerable,
        "avg_latency_ms": avg_latency,
    }
