"""
Failover behavior for router.chat().

The router does two-level rotation in providers.json priority order:
  1. rotate a provider's models (default first)
  2. when a provider is exhausted, fall over to the next provider

Status handling:
  401 / 403                -> skip the WHOLE provider (bad/expired key)
  429 / 404 / 5xx / timeout -> retryable: next model, then next provider
"""

import pytest

from tollfree import router


# Default models of the first three providers, for readable assertions.
GROQ_DEFAULT = "llama-3.3-70b-versatile"
GROQ_SECOND = "llama-3.1-8b-instant"
CEREBRAS_DEFAULT = "llama-3.3-70b"


def test_happy_path_uses_first_provider_first_model(router_sim):
    status, provider, model, text = router_sim({})
    assert status == "ok"
    assert (provider, model) == ("groq", GROQ_DEFAULT)
    assert text == f"<reply via {GROQ_DEFAULT}>"


def test_model_rotation_stays_within_provider(router_sim):
    # only groq's default model is rate-limited -> its 2nd model should answer
    status, provider, model, _ = router_sim({f"groq/{GROQ_DEFAULT}": 429})
    assert status == "ok"
    assert (provider, model) == ("groq", GROQ_SECOND)


def test_provider_exhausted_falls_over_to_next(router_sim):
    # every groq model 429 -> fall over to cerebras
    status, provider, model, _ = router_sim({"groq": 429})
    assert status == "ok"
    assert (provider, model) == ("cerebras", CEREBRAS_DEFAULT)


@pytest.mark.parametrize("bad_key_status", [401, 403])
def test_auth_error_skips_whole_provider(router_sim, bad_key_status):
    # 401/403 must skip groq entirely (not try its other models) -> cerebras
    status, provider, model, _ = router_sim({"groq": bad_key_status})
    assert status == "ok"
    assert provider == "cerebras"


@pytest.mark.parametrize("retryable", [429, 404, 500, 502, 503, "timeout", "conn"])
def test_retryable_outcomes_advance_one_model(router_sim, retryable):
    # groq default fails with a retryable outcome; its 2nd model still answers
    status, provider, model, _ = router_sim({f"groq/{GROQ_DEFAULT}": retryable})
    assert status == "ok"
    assert (provider, model) == ("groq", GROQ_SECOND)


def test_cascade_across_multiple_providers(router_sim):
    status, provider, _, _ = router_sim(
        {"groq": 429, "cerebras": 500, "google": 404}
    )
    assert status == "ok"
    assert provider == "openrouter"


def test_missing_key_skips_provider_without_http(router_sim):
    # no groq key -> skip straight to cerebras
    keys = [p["key_env"] for p in router.PROVIDERS if p["name"] != "groq"]
    status, provider, _, _ = router_sim({}, keys=keys)
    assert status == "ok"
    assert provider == "cerebras"


def test_all_providers_fail_raises_with_diagnostics(router_sim):
    status, detail = router_sim({p["name"]: 500 for p in router.PROVIDERS})
    assert status == "fail"
    # every model on every provider should appear in the aggregated error
    for p in router.PROVIDERS:
        for m in p["models"]:
            assert f"{p['name']}/{m}" in detail


def test_no_keys_at_all_raises(router_sim):
    status, detail = router_sim({}, keys=[])
    assert status == "fail"
    # each provider skipped for a missing key
    for p in router.PROVIDERS:
        assert p["key_env"] in detail


def test_priority_order_matches_registry(router_sim):
    # sanity: the first provider tried is the first in providers.json
    status, provider, _, _ = router_sim({})
    assert provider == router.PROVIDERS[0]["name"]
