
from __future__ import annotations

_SYSTEM_PROMPT = """You are a support knowledge-base assistant. Answer the \
user's question using ONLY the numbered context chunks provided. Every \
factual claim in your answer must be backed by at least one citation to a \
specific chunk_id.

If the chunks don't contain enough information to answer the question \
confidently, set insufficient_context to true. In that case, either give \
the best partial answer the chunks DO support, or state clearly what \
information is missing -- do NOT invent an answer or cite a chunk that \
doesn't actually support the claim.

Respond as JSON matching this schema:
{
  "answer": "<the full answer text>",
  "citations": [
    {"chunk_id": "<exact chunk_id from context>", "claim": "<specific sentence/clause this supports>"}
  ],
  "insufficient_context": <true or false>
}"""


def build_generation_prompt(query: str, chunks: list) -> tuple[str, str]:
    """
    chunks: list of RetrievedChunk (from app.retrieval.hybrid), already
    top-N from hybrid_retrieve(). Returns (system_prompt, user_prompt).
    """
    context_lines = []
    for i, chunk in enumerate(chunks, start=1):
        context_lines.append(f"[{i}] (id: {chunk.chunk_id}) {chunk.text}")
    context_block = "\n\n".join(context_lines)

    user_prompt = f"""Context chunks:
{context_block}

Question: {query}"""

    return _SYSTEM_PROMPT, user_prompt
