import re
import time
from groq import Groq
from groq import RateLimitError
from app.core.config import GROQ_API_KEY, GROQ_MODEL

_groq = Groq(api_key=GROQ_API_KEY)


class _Completions:
    """Wraps Groq completions with automatic retry on 429 rate-limit errors."""

    def create(self, model: str, messages: list, temperature: float = 0,
               max_tokens: int = None, **kwargs):
        kwargs_clean = {k: v for k, v in kwargs.items()}
        if max_tokens:
            kwargs_clean["max_tokens"] = max_tokens

        max_retries = 4
        for attempt in range(max_retries):
            try:
                return _groq.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    **kwargs_clean,
                )
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise
                # Parse suggested retry delay from error message
                match = re.search(r"try again in ([\d.]+)s", str(e), re.IGNORECASE)
                wait = float(match.group(1)) if match else (2 ** attempt) * 5
                wait = min(wait + 1, 60)
                print(f"[llm] Rate limited (attempt {attempt+1}/{max_retries}), retrying in {wait:.1f}s…")
                time.sleep(wait)


class _Chat:
    def __init__(self):
        self.completions = _Completions()


class _Client:
    def __init__(self):
        self.chat = _Chat()


client = _Client()