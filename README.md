# free-llm-router

A tiny abstraction over free-tier LLM API providers. One `chat()` call, keys read
straight from `.env`, with automatic failover: **rotate a provider's models first,
then fall over to the next provider.**

Almost every free provider (Groq, Cerebras, Google Gemini, OpenRouter, Mistral,
Z.AI, Together, DeepInfra, …) speaks the same OpenAI-compatible
`/chat/completions` API — so there's a single HTTP call and the only per-provider
data is `base_url` + key env var + model list.

## Install

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
cp .env.example .env   # fill in the keys you have
```

Missing keys are skipped automatically — you only need one to start.

## Use

```python
from router import chat

reply = chat("Explain the CAP theorem in two sentences.")

# with metadata about which provider/model actually answered:
reply, meta = chat("hi", return_meta=True, temperature=0.2)
# meta -> {'provider': 'google', 'model': 'gemini-3.6-flash'}
```

Or from the shell:

```bash
./.venv/bin/python router.py "your prompt here"
```

## Failover logic

```
for provider in PROVIDERS:          # priority order, set in providers.py
  for model in provider.models:     # default = first
    try  -> return on success
    401/403        -> skip whole provider (bad key)
    429/404/5xx/timeout -> next model, then next provider
raise AllProvidersFailed            # only when everything is exhausted
```

## Verify keys & limits — for free

`probe.py` checks every provider **without spending completion tokens**: it calls
`GET /models` (verifies the key + lists live models) and prints any rate-limit
response headers the provider returns.

```bash
./.venv/bin/python probe.py
```

## Configure

Edit `providers.py`:

- **Reorder priority** → reorder the `PROVIDERS` list.
- **Change a default model** → reorder that provider's `models` (first = default).
- **Add a provider** → copy a block, set `base_url` / `key_env` / `models`, add the
  key to `.env`.

> ⚠️ Free-tier model names churn fast. If a model 404s, run `probe.py` — the API
> usually names the current replacement in the error.

## Provider list from

[nejib1/Free-LLM](https://github.com/nejib1/Free-LLM) — a catalog of free-tier LLM
API providers.
