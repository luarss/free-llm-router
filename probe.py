"""
Probe providers WITHOUT spending completion quota.

For each provider that has a key in .env, this:
  - GET /models          -> verifies the key + auth, lists available models
                            (free; does not consume chat/token quota)
  - prints any rate-limit headers the provider returns (real remaining quota)
  - for OpenRouter, also GET /key for credit/limit/usage

Run:  ./.venv/bin/python probe.py
"""

import os
import requests
from dotenv import load_dotenv

from providers import PROVIDERS

load_dotenv()

# Header names providers use to advertise limits/quota. We match loosely.
_LIMIT_HINTS = ("ratelimit", "rate-limit", "retry-after", "x-request", "quota")

_TIMEOUT = 20


def _limit_headers(headers):
    out = {}
    for k, v in headers.items():
        lk = k.lower()
        if any(h in lk for h in _LIMIT_HINTS):
            out[k] = v
    return out


def probe(provider):
    key = os.getenv(provider["key_env"])
    name = provider["name"]
    if not key:
        print(f"— {name:12s} SKIP  (no {provider['key_env']} in .env)")
        return

    try:
        r = requests.get(
            f"{provider['base_url']}/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=_TIMEOUT,
        )
    except requests.RequestException as e:
        print(f"✘ {name:12s} NET   ({e})")
        return

    if r.status_code == 200:
        try:
            models = r.json().get("data", [])
            n = len(models)
        except ValueError:
            n = "?"
        print(f"✔ {name:12s} OK    key valid, {n} models visible")
    elif r.status_code in (401, 403):
        print(f"✘ {name:12s} AUTH  HTTP {r.status_code} — bad/expired key")
    else:
        print(f"⚠ {name:12s} HTTP {r.status_code} — {r.text[:80]}")

    for hk, hv in _limit_headers(r.headers).items():
        print(f"      · {hk}: {hv}")

    # OpenRouter exposes exact limit/usage/credit for free.
    if name == "openrouter" and r.status_code == 200:
        try:
            kr = requests.get(
                "https://openrouter.ai/api/v1/key",
                headers={"Authorization": f"Bearer {key}"},
                timeout=_TIMEOUT,
            ).json().get("data", {})
            print(
                f"      · usage=${kr.get('usage')} limit=${kr.get('limit')} "
                f"free_tier={kr.get('is_free_tier')}"
            )
        except requests.RequestException:
            pass


if __name__ == "__main__":
    print("Probing providers (no completion tokens spent)\n")
    for p in PROVIDERS:
        probe(p)
