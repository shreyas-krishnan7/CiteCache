
from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.config import settings

T = TypeVar("T", bound=BaseModel)

_JSON_INSTRUCTION = (
    "\n\nRespond with ONLY valid JSON matching the schema described above. "
    "No markdown code fences, no explanation text before or after the JSON."
)


def _call_openai(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    if not settings.openai_api_key:
        raise RuntimeError(
            "LLM_PROVIDER=openai but OPENAI_API_KEY is not set. "
            "Set it in .env, or switch LLM_PROVIDER to 'anthropic' or 'groq'."
        )
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=max_tokens,
        temperature=settings.generation_temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def _call_groq(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    """
    Groq exposes an OpenAI-compatible /chat/completions endpoint, so
    this reuses the `openai` package already in requirements.txt --
    just pointed at Groq's base_url with a Groq API key. No new
    dependency needed. Groq's free tier is generous enough to fully
    exercise this pipeline without a paid OpenAI/Anthropic account.
    """
    if not settings.groq_api_key:
        raise RuntimeError(
            "LLM_PROVIDER=groq but GROQ_API_KEY is not set. "
            "Get a free key at https://console.groq.com/keys and add it to .env."
        )
    from openai import OpenAI

    client = OpenAI(api_key=settings.groq_api_key, base_url="https://api.groq.com/openai/v1")
    response = client.chat.completions.create(
        model=settings.groq_model,
        max_tokens=max_tokens,
        temperature=settings.generation_temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def _call_anthropic(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set. "
            "Set it in .env, or set LLM_PROVIDER=openai and OPENAI_API_KEY instead."
        )
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        temperature=settings.generation_temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in response.content if hasattr(block, "text"))


def _call_gemini(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    """
    Gemini also exposes an OpenAI-compatible endpoint, same pattern as
    Groq -- reuses the `openai` package, just a different base_url and
    key. Gemini's free tier (no credit card, no expiry) is the other
    solid option alongside Groq if you're avoiding paid OpenAI/Anthropic.
    """
    if not settings.gemini_api_key:
        raise RuntimeError(
            "LLM_PROVIDER=gemini but GEMINI_API_KEY is not set. "
            "Get a free key at https://aistudio.google.com/apikey and add it to .env."
        )
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    response = client.chat.completions.create(
        model=settings.gemini_model,
        max_tokens=max_tokens,
        temperature=settings.generation_temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    """Raw text completion. Dispatches on settings.llm_provider."""
    if settings.llm_provider == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, max_tokens)
    if settings.llm_provider == "groq":
        return _call_groq(system_prompt, user_prompt, max_tokens)
    if settings.llm_provider == "gemini":
        return _call_gemini(system_prompt, user_prompt, max_tokens)
    return _call_openai(system_prompt, user_prompt, max_tokens)


def _extract_json(raw: str) -> str:
    """Strips markdown code fences if the model added them despite instructions."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def call_structured(
    system_prompt: str,
    user_prompt: str,
    schema: type[T],
    max_tokens: int,
    max_retries: int | None = None,
) -> T:
    """
    Calls the LLM and parses the response into `schema` (a Pydantic
    model). On invalid JSON or a schema mismatch, retries with the
    validation error appended to the prompt so the model can correct
    itself -- this is what makes generation/verification robust
    against the occasional malformed response instead of crashing
    the whole pipeline run on one bad completion.
    """
    max_retries = max_retries if max_retries is not None else settings.structured_output_max_retries
    full_system_prompt = system_prompt + _JSON_INSTRUCTION
    current_user_prompt = user_prompt
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        raw = call_llm(full_system_prompt, current_user_prompt, max_tokens)
        cleaned = _extract_json(raw)
        try:
            data = json.loads(cleaned)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            current_user_prompt = (
                f"{user_prompt}\n\n"
                f"Your previous response could not be parsed: {e}\n"
                f"Previous response was: {cleaned[:500]}\n"
                f"Try again. Respond with ONLY valid JSON matching the schema."
            )

    raise RuntimeError(
        f"Failed to get valid structured output from LLM after {max_retries + 1} attempts. "
        f"Last error: {last_error}"
    )
