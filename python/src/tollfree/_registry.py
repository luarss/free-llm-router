"""Load the canonical provider registry bundled with the package.

The registry lives in providers.json (kept in sync from the repo root by
scripts/sync-providers). Loading it here keeps a single source of truth.
"""

import json
from importlib.resources import files


def load_providers():
    """Return the provider list from the bundled providers.json."""
    raw = files(__package__).joinpath("providers.json").read_text(encoding="utf-8")
    return json.loads(raw)["providers"]


PROVIDERS = load_providers()
