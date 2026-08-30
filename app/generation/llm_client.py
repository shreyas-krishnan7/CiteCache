
from __future__ import annotations

import json
import re
import time
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
            "Set it in .env, or switch LLM_PROVIDER to 'anthropic', 'groq', or 'gemini'."
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


def _call_anthropic(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set. "
            "Set it in .env, or switch LLM_PROVIDER to 'openai', 'groq', or 'gemini'."
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


def _call_groq(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
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


def _call_gemini(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
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


_PROVIDER_DISPATCH = {
    "anthropic": _call_anthropic,
    "groq": _call_groq,
    "gemini": _call_gemini,
    "openai": _call_openai,
}


def _is_rate_limit_error(e: Exception) -> bool:
    """
    Deliberately doesn't import each provider's specific exception
    class (openai.RateLimitError, anthropic.RateLimitError, etc.) --
    checking the exception's type name and message keeps this
    provider-agnostic, same philosophy as the rest of this file.
    """
    name = type(e).__name__
    text = str(e)
    return (
        "RateLimitError" in name
        or "429" in text
        or "RESOURCE_EXHAUSTED" in text
        or "rate limit" in text.lower()
        or "quota" in text.lower()
    )


def _extract_retry_delay_seconds(e: Exception, default: float) -> float:
    """
    Providers often tell you exactly how long to wait (e.g. Gemini's
    "Please retry in 11.798004596s" or a Retry-After header baked into
    the error body). Use it when present; fall back to a configured
    default otherwise. A small buffer is added since the suggested
    delay is usually a minimum, not a guarantee.
    """
    match = re.search(r"retry[- ]?(?:after|in)\D{0,5}(\d+(?:\.\d+)?)", str(e), re.IGNORECASE)
    if match:
        return float(match.group(1)) + 1.0
    return default


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int, provider: str | None = None) -> str:
    """
    Raw text completion. Dispatches on `provider` if given, else
    settings.llm_provider, with retry-with-backoff on rate-limit
    errors (up to llm_rate_limit_max_retries attempts). Non-rate-limit
    errors are raised immediately.
    """
    active_provider = provider or settings.llm_provider
    call_fn = _PROVIDER_DISPATCH.get(active_provider, _call_openai)
    max_retries = settings.llm_rate_limit_max_retries
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return call_fn(system_prompt, user_prompt, max_tokens)
        except Exception as e:
            if not _is_rate_limit_error(e) or attempt == max_retries:
                raise
            last_error = e
            delay = _extract_retry_delay_seconds(e, settings.llm_rate_limit_default_delay_seconds)
            print(f"  [llm_client] {active_provider} rate limit hit "
                  f"(attempt {attempt + 1}/{max_retries + 1}) -- waiting {delay:.1f}s before retrying...")
            time.sleep(delay)

    raise last_error  # unreachable in practice, keeps type checkers happy


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
    provider: str | None = None,
) -> T:
    """
    Calls the LLM and parses the response into `schema` (a Pydantic
    model). `provider` overrides settings.llm_provider for this call
    only -- used by app/eval/llm_judge.py to grade with a different
    (e.g. higher-rate-limit) provider than the one generating answers,
    without affecting generation or citation verification at all.
    On invalid JSON or a schema mismatch, retries with the validation
    error appended to the prompt so the model can correct itself.
    """
    max_retries = max_retries if max_retries is not None else settings.structured_output_max_retries
    full_system_prompt = system_prompt + _JSON_INSTRUCTION
    current_user_prompt = user_prompt
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        raw = call_llm(full_system_prompt, current_user_prompt, max_tokens, provider=provider)
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
