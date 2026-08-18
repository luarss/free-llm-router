# tollfree (Python)

One `chat()` call over free-tier LLM providers, with automatic failover:
**rotate a provider's models first, then fall over to the next provider.**

Keys are read straight from `.env`. Missing keys are skipped automatically — you
only need one to start.

## Install

```bash
pip install tollfree     # or: uv add tollfree
```

## Use

```python
from tollfree import chat

reply = chat("Explain the CAP theorem in two sentences.")

# with metadata about which provider/model actually answered:
reply, meta = chat("hi", return_meta=True, temperature=0.2)
# meta -> {'provider': 'google', 'model': 'gemini-3.6-flash'}
```

CLI:

```bash
tollfree "your prompt here"   # chat
tollfree probe                # verify keys + limits, spends no completion tokens
```

## Failover logic

```
for provider in PROVIDERS:          # priority order (providers.json)
  for model in provider.models:     # default = first
    try  -> return on success
    401/403             -> skip whole provider (bad key)
    429/404/5xx/timeout -> next model, then next provider
raise AllProvidersFailed            # only when everything is exhausted
```

## Configuration

Set keys in `.env` (or the environment):

```
GROQ_API_KEY=
CEREBRAS_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
MISTRAL_API_KEY=
ZAI_API_KEY=
```

The provider/model registry is `providers.json`, kept in sync from the
[central repo](https://github.com/luarss/free-llm-router) which is the source of
truth for both the Python and npm packages.
