/**
 * tollfree router: one chat() call, automatic model + provider failover.
 *
 * Rotation order:
 *   1. Within a provider, rotate through its models (default first).
 *   2. When a provider's models are all exhausted, fall over to the next provider.
 *
 * Usage:
 *   import { chat } from "tollfree";
 *   const reply = await chat("Explain CAP theorem in two sentences.");
 *
 *   const { text, meta } = await chat({
 *     messages: [{ role: "user", content: "hi" }],
 *     temperature: 0.2,
 *     returnMeta: true,
 *   });
 *   // meta -> { provider: "groq", model: "llama-3.3-70b-versatile" }
 */
import "dotenv/config"; // pulls keys from .env in cwd

import { PROVIDERS, Provider } from "./registry";

export { PROVIDERS, Provider } from "./registry";
export { probe, probeAll } from "./probe";

export interface Message {
  role: string;
  content: string;
}

export interface ChatMeta {
  provider: string;
  model: string;
}

export interface ChatOptions {
  prompt?: string;
  messages?: Message[];
  returnMeta?: boolean;
  verbose?: boolean;
  /** Extra params (temperature, max_tokens, ...) forwarded to the API verbatim. */
  [param: string]: unknown;
}

/** Raised when every configured model on every provider failed. */
export class AllProvidersFailed extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AllProvidersFailed";
  }
}

// HTTP statuses meaning "this key/provider is unusable — skip the whole provider".
const SKIP_PROVIDER_STATUSES = new Set([401, 403]);
// Any other >=400 is retryable: try next model, then next provider.

const TIMEOUT_MS = 60_000;

class SkipProvider extends Error {}
class TryNextModel extends Error {}

const KNOWN_KEYS = new Set(["prompt", "messages", "returnMeta", "verbose"]);

function extraParams(options: ChatOptions): Record<string, unknown> {
  const params: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(options)) {
    if (!KNOWN_KEYS.has(k)) params[k] = v;
  }
  return params;
}

async function call(
  provider: Provider,
  model: string,
  messages: Message[],
  params: Record<string, unknown>,
): Promise<string> {
  const key = process.env[provider.key_env];
  if (!key) throw new SkipProvider(`no key (${provider.key_env}) in env`);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let resp: Response;
  try {
    resp = await fetch(`${provider.base_url}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model, messages, ...params }),
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }

  if (SKIP_PROVIDER_STATUSES.has(resp.status)) {
    throw new SkipProvider(`HTTP ${resp.status}: ${(await resp.text()).slice(0, 200)}`);
  }
  if (resp.status >= 400) {
    // retryable at the model level (bad model name, rate limit, 5xx, ...)
    throw new TryNextModel(`HTTP ${resp.status}: ${(await resp.text()).slice(0, 200)}`);
  }

  const data = (await resp.json()) as {
    choices: { message: { content: string } }[];
  };
  return data.choices[0].message.content;
}

export async function chat(
  prompt: string,
  options?: Omit<ChatOptions, "prompt">,
): Promise<string>;
export async function chat(options: ChatOptions): Promise<string | { text: string; meta: ChatMeta }>;
export async function chat(
  promptOrOptions: string | ChatOptions,
  maybeOptions?: Omit<ChatOptions, "prompt">,
): Promise<string | { text: string; meta: ChatMeta }> {
  const options: ChatOptions =
    typeof promptOrOptions === "string"
      ? { prompt: promptOrOptions, ...maybeOptions }
      : promptOrOptions;

  let messages = options.messages;
  if (!messages) {
    if (options.prompt === undefined) {
      throw new Error("provide either `prompt` or `messages`");
    }
    messages = [{ role: "user", content: options.prompt }];
  }

  const params = extraParams(options);
  const errors: string[] = []; // "provider/model: reason" for diagnostics

  for (const provider of PROVIDERS) {
    let skipProvider = false;
    for (const model of provider.models) {
      try {
        const text = await call(provider, model, messages, params);
        if (options.verbose) console.error(`[ok] ${provider.name} / ${model}`);
        if (options.returnMeta) {
          return { text, meta: { provider: provider.name, model } };
        }
        return text;
      } catch (e) {
        if (e instanceof SkipProvider) {
          if (options.verbose) console.error(`[skip provider] ${provider.name}: ${e.message}`);
          errors.push(`${provider.name}/*: ${e.message}`);
          skipProvider = true;
          break; // stop trying this provider's other models
        } else if (e instanceof TryNextModel) {
          if (options.verbose) console.error(`[next model] ${provider.name} / ${model}: ${e.message}`);
          errors.push(`${provider.name}/${model}: ${e.message}`);
        } else {
          // network / abort / parse error — try next model, then next provider
          const msg = e instanceof Error ? e.message : String(e);
          if (options.verbose) console.error(`[network] ${provider.name} / ${model}: ${msg}`);
          errors.push(`${provider.name}/${model}: network: ${msg}`);
        }
      }
    }
    void skipProvider;
  }

  const detail = errors.length ? errors.map((e) => `  ${e}`).join("\n") : "  (no keys found)";
  throw new AllProvidersFailed(`All providers/models failed:\n${detail}`);
}
