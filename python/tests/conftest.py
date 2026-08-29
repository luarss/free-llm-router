"""
Shared test harness for the failover suite.

We never hit a real API. Instead we patch the two things router._call touches:
  - the key lookup (os.getenv), so we control which providers "have keys"
  - requests.post, so we script an HTTP outcome per provider / per model

`router_sim` yields a helper that runs router.chat() against a rule set and
returns the parsed result, so each test reads as: given these outcomes, the
router should land on this provider/model (or raise AllProvidersFailed).
"""

import pytest
import requests

from tollfree import router


class FakeResp:
    def __init__(self, status, model):
        self.status_code = status
        self._model = model
        self.text = f'{{"error":"simulated HTTP {status}"}}'

    def json(self):
        return {"choices": [{"message": {"content": f"<reply via {self._model}>"}}]}


def _provider_of(url):
    return next(p["name"] for p in router.PROVIDERS if p["base_url"] in url)


def _resolve(rules, provider, model):
    """First matching rule wins; 'provider/model' beats 'provider'. Default 200."""
    return rules.get(f"{provider}/{model}", rules.get(provider, 200))


@pytest.fixture
def router_sim(monkeypatch):
    """
    Return run(rules, keys=...) -> ("ok", provider, model) | ("fail", AllProvidersFailed).

    rules maps a matcher to an outcome:
      matcher: "provider" | "provider/model"
      outcome: int status code | "timeout" | "conn"
    keys: iterable of key_env names that are "present" (default: all providers).
    """

    def run(rules, keys=None):
        present = (
            {p["key_env"] for p in router.PROVIDERS} if keys is None else set(keys)
        )
        env = {
            p["key_env"]: "sk-fake"
            for p in router.PROVIDERS
            if p["key_env"] in present
        }

        def fake_getenv(name, default=None):
            return env.get(name, default)

        def fake_post(url, headers=None, json=None, timeout=None):
            provider = _provider_of(url)
            outcome = _resolve(rules, provider, json["model"])
            if outcome == "timeout":
                raise requests.Timeout("simulated timeout")
            if outcome == "conn":
                raise requests.ConnectionError("simulated connection drop")
            return FakeResp(outcome, json["model"])

        monkeypatch.setattr(router.os, "getenv", fake_getenv)
        monkeypatch.setattr(router.requests, "post", fake_post)

        try:
            text, meta = router.chat("ping", return_meta=True)
            return ("ok", meta["provider"], meta["model"], text)
        except router.AllProvidersFailed as e:
            return ("fail", str(e))

    return run
