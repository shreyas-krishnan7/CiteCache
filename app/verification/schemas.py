
from __future__ import annotations

from pydantic import BaseModel, Field


class CitationVerdict(BaseModel):
    chunk_id: str
    claim: str
    supported: bool
    reasoning: str = Field(description="One sentence explaining the verdict.")
    method: str = Field(description="'id_check', 'embedding_prefilter', or 'llm_judge' -- which stage produced this verdict.")


class _LLMJudgeVerdict(BaseModel):
    """What we actually ask the LLM for -- chunk_id/claim are already known, no need to have the model echo them back."""
    supported: bool
    reasoning: str
