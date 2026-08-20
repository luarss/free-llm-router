# tollfree — free-llm-router

A tiny abstraction over free-tier LLM API providers. One `chat()` call, keys read
straight from `.env`, with automatic failover: **rotate a provider's models first,
then fall over to the next provider.**

Almost every free provider (Groq, Cerebras, Google Gemini, OpenRouter, Mistral,
Z.AI, Together, DeepInfra, …) speaks the same OpenAI-compatible
`/chat/completions` API — so there's a single HTTP call and the only per-provider
data is `base_url` + key env var + model list.

This repo is the **central source of truth**. It ships the router as two packages
from one shared provider registry:

| Registry | Package | Directory | Install |
| --- | --- | --- | --- |
| PyPI | `tollfree` | [`python/`](python/) | `pip install tollfree` |
| npm | `tollfree` | [`js/`](js/) | `npm install tollfree` |

## Quickstart

Python:

```python
from tollfree import chat
reply, meta = chat("Explain the CAP theorem in two sentences.", return_meta=True)
# meta -> {'provider': 'google', 'model': 'gemini-3.6-flash'}
```

Node / TypeScript:

```ts
import { chat } from "tollfree";
const { text, meta } = await chat({ prompt: "Explain the CAP theorem.", returnMeta: true });
// meta -> { provider: "google", model: "gemini-3.6-flash" }
```

CLI (either package): `tollfree "your prompt"` to chat, `tollfree probe` to verify
keys and limits without spending completion tokens.

## Failover logic

```
for provider in PROVIDERS:          # priority order (providers.json)
  for model in provider.models:     # default = first
    try  -> return on success
    401/403             -> skip whole provider (bad key)
    429/404/5xx/timeout -> next model, then next provider
raise/throw AllProvidersFailed      # only when everything is exhausted
```

## How this differs from LiteLLM

Same category — a unified interface over many OpenAI-compatible providers — but a
very different scope. `tollfree` is built around one job: **stay on free tiers.**

| | tollfree | LiteLLM |
| --- | --- | --- |
| Core purpose | Chain free-tier providers so you never pay | General provider-agnostic routing (paid & free) |
| Failover | Rotate a provider's models, then the next provider | Retries, fallbacks, load balancing, routing strategies |
| Config | One `providers.json`, keys from `.env` | YAML/env, model aliases, per-key budgets |
| Extras | `probe` to check keys/limits | Cost tracking, caching, rate limiting, logging, virtual keys, embeddings, a hosted proxy |
| Surface area | Tiny (two thin packages) | Full SDK + proxy framework, 100+ providers |

Reach for LiteLLM when you need production infrastructure — spend tracking,
streaming, embeddings, a shared gateway. Reach for `tollfree` when you just want a
lightweight "never hit a paywall" router. The two aren't exclusive: you could use
`tollfree`'s ordered free-tier list to drive fallbacks *inside* LiteLLM.

## Single source of truth

[`providers.json`](providers.json) at the repo root is the canonical registry
(priority order, base URLs, key env vars, model lists). Both packages ship a copy;
regenerate them after editing the root file:

```bash
./scripts/sync-providers.sh
```

To add a provider, edit `providers.json` and re-run the sync. To change priority,
reorder the list. To change a default model, reorder its `models`.

> ⚠️ Free-tier model names churn fast. If a model 404s, run `tollfree probe` — the
> API usually names the current replacement in the error.

## Keys

Set the keys you have in `.env` (missing keys are skipped automatically):

```
GROQ_API_KEY=
CEREBRAS_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
MISTRAL_API_KEY=
ZAI_API_KEY=
```

## Developing / releasing

```bash
# Python
cd python && uv build            # -> python/dist/*.whl, *.tar.gz
#          uv publish            # needs PyPI token

# npm
cd js && npm install && npm run build   # -> js/dist/
#         npm publish                    # needs npm auth
```

Publishing auth (PyPI API token, npm token) is supplied at release time.

## Provider list from

[nejib1/Free-LLM](https://github.com/nejib1/Free-LLM) — a catalog of free-tier LLM
API providers.
