/**
 * Probe providers WITHOUT spending completion quota.
 *
 * For each provider that has a key in .env, this:
 *   - GET /models          -> verifies the key + auth, lists available models
 *                            (free; does not consume chat/token quota)
 *   - prints any rate-limit headers the provider returns
 *   - for OpenRouter, also GET /key for credit/limit/usage
 */
import "dotenv/config";

import { PROVIDERS, Provider } from "./registry";

// Header names providers use to advertise limits/quota. Matched loosely.
const LIMIT_HINTS = ["ratelimit", "rate-limit", "retry-after", "x-request", "quota"];

const TIMEOUT_MS = 20_000;

function limitHeaders(headers: Headers): [string, string][] {
  const out: [string, string][] = [];
  headers.forEach((v, k) => {
    const lk = k.toLowerCase();
    if (LIMIT_HINTS.some((h) => lk.includes(h))) out.push([k, v]);
  });
  return out;
}

function pad(name: string): string {
  return name.padEnd(12, " ");
}

export async function probe(provider: Provider): Promise<void> {
  const key = process.env[provider.key_env];
  const name = provider.name;
  if (!key) {
    console.log(`— ${pad(name)} SKIP  (no ${provider.key_env} in .env)`);
    return;
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let r: Response;
  try {
    r = await fetch(`${provider.base_url}/models`, {
      headers: { Authorization: `Bearer ${key}` },
      signal: controller.signal,
    });
  } catch (e) {
    console.log(`✘ ${pad(name)} NET   (${e instanceof Error ? e.message : String(e)})`);
    return;
  } finally {
    clearTimeout(timer);
  }

  if (r.status === 200) {
    let n: number | string = "?";
    try {
      const body = (await r.clone().json()) as { data?: unknown[] };
      n = body.data?.length ?? "?";
    } catch {
      n = "?";
    }
    console.log(`✔ ${pad(name)} OK    key valid, ${n} models visible`);
  } else if (r.status === 401 || r.status === 403) {
    console.log(`✘ ${pad(name)} AUTH  HTTP ${r.status} — bad/expired key`);
  } else {
    console.log(`⚠ ${pad(name)} HTTP ${r.status} — ${(await r.text()).slice(0, 80)}`);
  }

  for (const [hk, hv] of limitHeaders(r.headers)) {
    console.log(`      · ${hk}: ${hv}`);
  }

  // OpenRouter exposes exact limit/usage/credit for free.
  if (name === "openrouter" && r.status === 200) {
    try {
      const kr = (await fetch("https://openrouter.ai/api/v1/key", {
        headers: { Authorization: `Bearer ${key}` },
      }).then((x) => x.json())) as { data?: Record<string, unknown> };
      const d = kr.data ?? {};
      console.log(
        `      · usage=$${d.usage} limit=$${d.limit} free_tier=${d.is_free_tier}`,
      );
    } catch {
      // ignore
    }
  }
}

export async function probeAll(): Promise<void> {
  console.log("Probing providers (no completion tokens spent)\n");
  for (const p of PROVIDERS) {
    await probe(p);
  }
}
