/**
 * Canonical provider registry, inlined at build time from providers.json
 * (kept in sync from the repo root by scripts/sync-providers). Single source
 * of truth shared with the Python package.
 */
import registry from "./providers.json";

export interface Provider {
  name: string;
  base_url: string;
  key_env: string;
  models: string[];
}

export const PROVIDERS: Provider[] = registry.providers as Provider[];
