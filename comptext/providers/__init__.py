from .google import GoogleProvider
from .xai import XAIProvider
from .nvidia import NVIDIAProvider
from .exceptions import (
    ProviderError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderConnectionError,
    ProviderAPIError
)

_MAP = {
    "google": GoogleProvider,
    "xai": XAIProvider,
    "nvidia": NVIDIAProvider,
}

def get_provider(name: str, **kwargs):
    """Retrieve an initialized provider instance by name."""
    if name not in _MAP:
        raise ValueError(f"Unknown provider: {name}")
    return _MAP[name](**kwargs)
