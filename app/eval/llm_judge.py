"""
LLM-as-judge answer correctness.

Grades a generated answer against a reference answer semantically,
not by string/keyword matching -- this is what fixes the exact
blind spot the keyword-based scorer had (e.g. marking "retried three
times over seven days" WRONG because it didn't contain the literal
substrings "3 times"/"7 days").

Deliberately built on the same provider-agnostic call_structured()
already used for generation and citation verification, rather than
adopting the RAGAS library. RAGAS's standard metrics (faithfulness,
answer relevancy, context precision/recall) typically fire several
LLM calls each per question; for a 29-question eval already
constrained by free-tier rate limits, that's a real cost, not a
theoretical one. This module gets the specific thing that was broken
(semantic answer grading) for one extra call per answerable question.
If you want RAGAS's full metric suite later, this is a clean
boundary to swap in -- score_question() in metrics.py calls exactly
one function here, judge_answer(), that a RAGAS-based implementation
could replace without touching anything else in the eval pipeline.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.config import settings
from app.generation.llm_client import call_structured

_JUDGE_SYSTEM_PROMPT = """You are grading whether a CANDIDATE ANSWER conveys the \
same substantive information as a REFERENCE ANSWER, for a given QUESTION.

Grade on substance, not wording. The candidate does NOT need to match the \
reference word-for-word -- different phrasing, spelled-out numbers instead \
of digits, different sentence structure, or additional correct detail are \
all fine. Mark it INCORRECT only if the candidate is missing a material \
fact the reference contains, states something that contradicts the \
reference, or fails to actually answer the question asked.

Respond as JSON matching this schema:
{"correct": <true or false>, "reasoning": "<one sentence>"}"""


class AnswerJudgeVerdict(BaseModel):
    correct: bool
    reasoning: str


def judge_answer(question: str, reference_answer: str, candidate_answer: str) -> AnswerJudgeVerdict:
    user_prompt = (
        f"QUESTION: {question}\n\n"
        f"REFERENCE ANSWER: {reference_answer}\n\n"
        f"CANDIDATE ANSWER: {candidate_answer}"
    )
    judge_provider = settings.eval_judge_provider or settings.llm_provider
    return call_structured(
        system_prompt=_JUDGE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=AnswerJudgeVerdict,
        max_tokens=settings.verification_max_tokens,
        provider=judge_provider,
    )
