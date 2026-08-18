# TODO

Publish this as an npm/PyPI SDK (`tollfree`) so downstream repos with frequent LLM
usage can depend on it. This repo is the central source of truth for router logic,
provider config, and failover.

## Done
- [x] Extract canonical `providers.json` (shared registry) + sync script
- [x] Python package `tollfree` in `python/` — builds, imports, CLI verified
- [x] npm package `tollfree` in `js/` (TS port) — builds, imports, CLI verified
- [x] Root README / docs cover both packages + source-of-truth model

## Remaining (needs auth)
- [ ] Reserve/publish to PyPI: `cd python && uv publish` (needs PyPI API token)
- [ ] Publish to npm: `cd js && npm publish` (needs `npm login` / npm token)
- [ ] Tag a release (e.g. `v0.1.0`) once both are live
- [ ] (optional) CI: run `scripts/sync-providers.sh` and fail if copies drift
