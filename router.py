"""
Free-LLM router: one chat() call, automatic model + provider failover.

Rotation order (as requested):
  1. Within a provider, rotate through its models (default first).
  2. When a provider's models are all exhausted, fall over to the next provider.

Usage:
    from router import chat
    reply = chat("Explain CAP theorem in two sentences.")
    print(reply)

    # or with full message history / options
    reply, meta = chat(
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.2,
        return_meta=True,
    )
    print(meta)  # {'provider': 'groq', 'model': 'llama-3.3-70b-versatile'}
"""

import os
import requests
from dotenv import load_dotenv

from providers import PROVIDERS

load_dotenv()  # pulls keys from .env in cwd

# HTTP statuses that mean "this key/provider is unusable — skip the whole provider"
_SKIP_PROVIDER_STATUSES = {401, 403}
# Any other >=400 is treated as retryable: try next model, then next provider.

_TIMEOUT = 60  # seconds per request


class AllProvidersFailed(Exception):
    """Raised when every configured model on every provider failed."""


def _call(provider, model, messages, **params):
    """Single OpenAI-compatible request. Returns assistant text or raises."""
    key = os.getenv(provider["key_env"])
    if not key:
        raise _SkipProvider(f"no key ({provider['key_env']}) in env")

    resp = requests.post(
        f"{provider['base_url']}/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json={"model": model, "messages": messages, **params},
        timeout=_TIMEOUT,
    )

    if resp.status_code in _SKIP_PROVIDER_STATUSES:
        raise _SkipProvider(f"HTTP {resp.status_code}: {resp.text[:200]}")
    if resp.status_code >= 400:
        # retryable at the model level (bad model name, rate limit, 5xx, ...)
        raise _TryNextModel(f"HTTP {resp.status_code}: {resp.text[:200]}")

    return resp.json()["choices"][0]["message"]["content"]


class _SkipProvider(Exception):
    pass


class _TryNextModel(Exception):
    pass


def chat(prompt=None, messages=None, return_meta=False, verbose=False, **params):
    """
    Send a chat request, failing over across models then providers.

    Pass either `prompt` (str) or `messages` (OpenAI-format list). Extra kwargs
    (temperature, max_tokens, ...) are forwarded to the API verbatim.
    """
    if messages is None:
        if prompt is None:
            raise ValueError("provide either `prompt` or `messages`")
        messages = [{"role": "user", "content": prompt}]

    errors = []  # (provider, model, reason) for diagnostics

    for provider in PROVIDERS:
        for model in provider["models"]:
            try:
                text = _call(provider, model, messages, **params)
                if verbose:
                    print(f"[ok] {provider['name']} / {model}")
                if return_meta:
                    return text, {"provider": provider["name"], "model": model}
                return text
            except _SkipProvider as e:
                if verbose:
                    print(f"[skip provider] {provider['name']}: {e}")
                errors.append((provider["name"], "*", str(e)))
                break  # stop trying this provider's other models
            except _TryNextModel as e:
                if verbose:
                    print(f"[next model] {provider['name']} / {model}: {e}")
                errors.append((provider["name"], model, str(e)))
                continue
            except (requests.Timeout, requests.ConnectionError) as e:
                if verbose:
                    print(f"[network] {provider['name']} / {model}: {e}")
                errors.append((provider["name"], model, f"network: {e}"))
                continue

    detail = "\n".join(f"  {p}/{m}: {r}" for p, m, r in errors) or "  (no keys found)"
    raise AllProvidersFailed(f"All providers/models failed:\n{detail}")


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "Say hello in one short sentence."
    answer, meta = chat(q, return_meta=True, verbose=True)
    print(f"\n--- {meta['provider']} / {meta['model']} ---")
    print(answer)
