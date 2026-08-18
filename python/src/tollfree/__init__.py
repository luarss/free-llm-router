"""tollfree — one chat() call over free-tier LLM providers, with automatic
model + provider failover. See https://github.com/luarss/free-llm-router."""

from ._registry import PROVIDERS
from .probe import probe, probe_all
from .router import AllProvidersFailed, chat

__all__ = ["chat", "probe", "probe_all", "PROVIDERS", "AllProvidersFailed"]
__version__ = "0.1.0"
