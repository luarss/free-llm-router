"""
Provider registry — priority order matters (top = tried first).

Every provider here speaks the OpenAI-compatible /chat/completions API, so the
only per-provider differences are: base_url, the env var holding the key, and the
list of model names (first model = the default, tried before falling back).

To add a provider: drop a block below and add its key to .env. To change
priority: reorder the list. To change the default model: reorder its `models`.
"""

PROVIDERS = [
    {
        "name": "groq",
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "models": [
            "llama-3.3-70b-versatile",   # default
            "llama-3.1-8b-instant",
            "qwen/qwen3-32b",
        ],
    },
    {
        "name": "cerebras",
        "base_url": "https://api.cerebras.ai/v1",
        "key_env": "CEREBRAS_API_KEY",
        "models": [
            "llama-3.3-70b",
            "llama3.1-8b",
            "qwen-3-32b",
        ],
    },
    {
        "name": "google",  # Gemini via its OpenAI-compatible endpoint
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_env": "GEMINI_API_KEY",
        "models": [
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
        ],
    },
    {
        "name": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemini-2.0-flash-exp:free",
        ],
    },
    {
        "name": "mistral",
        "base_url": "https://api.mistral.ai/v1",
        "key_env": "MISTRAL_API_KEY",
        "models": [
            "mistral-small-latest",
            "open-mistral-nemo",
        ],
    },
    {
        "name": "zai",  # Z.AI GLM
        "base_url": "https://api.z.ai/api/paas/v4",
        "key_env": "ZAI_API_KEY",
        "models": [
            "glm-4-flash",
        ],
    },
]
