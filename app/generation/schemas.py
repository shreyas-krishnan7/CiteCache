
from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
    chunk_id: str = Field(description="The exact chunk_id from the numbered context, e.g. the id shown in [1] (id: ...).")
    claim: str = Field(description="The specific sentence or clause from the answer that this citation supports.")


class GeneratedAnswer(BaseModel):
    answer: str = Field(description="The full answer to the user's question, grounded in the provided context.")
    citations: list[Citation] = Field(default_factory=list)
    insufficient_context: bool = Field(
        description="True if the provided context chunks do not contain enough information to answer confidently."
    )
