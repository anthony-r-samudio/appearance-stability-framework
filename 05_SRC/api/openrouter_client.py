import os

from openai import OpenAI, APIStatusError

_BASE_URL = "https://openrouter.ai/api/v1"


class CreditError(Exception):
    """Raised when OpenRouter returns HTTP 402 (insufficient credits or max_tokens too high)."""


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY environment variable is not set.\n"
            "Set it in PowerShell with:\n"
            '  $env:OPENROUTER_API_KEY="sk-or-v1-..."'
        )
    return OpenAI(base_url=_BASE_URL, api_key=api_key)


def generate_response(
    model:       str,
    prompt:      str,
    temperature: float    = 0.7,
    max_tokens:  "int | None" = None,
) -> str:
    """Send a prompt to a model on OpenRouter and return the text response."""
    client = _get_client()
    kwargs: dict = dict(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()


def score_output(
    model:          str,
    scoring_prompt: str,
    temperature:    float = 0.0,
    timeout:        float = 60.0,
    max_tokens:     int   = 800,
) -> str:
    """Send a scoring prompt to a judge model and return the raw text response."""
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": scoring_prompt}],
            temperature=temperature,
            timeout=timeout,
            max_tokens=max_tokens,
        )
    except APIStatusError as exc:
        if exc.status_code == 402:
            raise CreditError(
                "OpenRouter credit/max_tokens error (HTTP 402). "
                "Try lowering --max-tokens or adding credits."
            ) from exc
        raise
    return response.choices[0].message.content.strip()
