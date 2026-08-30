
from __future__ import annotations

from pydantic import BaseModel, Field


class CitationVerdict(BaseModel):
    chunk_id: str
    claim: str
    supported: bool
    reasoning: str = Field(description="One sentence explaining the verdict.")
    method: str = Field(description="'id_check', 'embedding_prefilter', or 'llm_judge_batched'.")


class _LLMJudgeVerdict(BaseModel):
    supported: bool
    reasoning: str


class _BatchJudgeItem(BaseModel):
    index: int
    supported: bool
    reasoning: str


class _BatchJudgeResponse(BaseModel):
    verdicts: list[_BatchJudgeItem]
