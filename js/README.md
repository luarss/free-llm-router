# tollfree (Node / TypeScript)

One `chat()` call over free-tier LLM providers, with automatic failover:
**rotate a provider's models first, then fall over to the next provider.**

Keys are read straight from `.env`. Missing keys are skipped automatically — you
only need one to start. Requires Node 18+ (uses the built-in `fetch`).

## Install

```bash
npm install tollfree
```

## Use

```ts
import { chat } from "tollfree";

const reply = await chat("Explain the CAP theorem in two sentences.");

// with metadata about which provider/model actually answered:
const { text, meta } = await chat({ prompt: "hi", returnMeta: true, temperature: 0.2 });
// meta -> { provider: "google", model: "gemini-3.6-flash" }
```

CLI:

```bash
npx tollfree "your prompt here"   # chat
npx tollfree probe                # verify keys + limits, spends no completion tokens
```

## Failover logic

```
for provider of PROVIDERS:          // priority order (providers.json)
  for model of provider.models:     // default = first
    try  -> return on success
    401/403             -> skip whole provider (bad key)
    429/404/5xx/timeout -> next model, then next provider
throw AllProvidersFailed            // only when everything is exhausted
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
truth for both the npm and Python packages.
