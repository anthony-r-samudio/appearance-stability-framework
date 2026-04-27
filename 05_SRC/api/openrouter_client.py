import os

from openai import OpenAI

_BASE_URL = "https://openrouter.ai/api/v1"


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY environment variable is not set.\n"
            "Set it in PowerShell with:\n"
            '  $env:OPENROUTER_API_KEY="sk-or-v1-..."'
        )
    return OpenAI(base_url=_BASE_URL, api_key=api_key)


def generate_response(model: str, prompt: str, temperature: float = 0.7) -> str:
    """Send a prompt to a model on OpenRouter and return the text response."""
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def score_output(model: str, scoring_prompt: str, temperature: float = 0.0) -> str:
    """Send a scoring prompt to a judge model and return the raw text response."""
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": scoring_prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()
