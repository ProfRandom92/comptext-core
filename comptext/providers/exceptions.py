class ProviderError(Exception):
    """Base exception for all LLM providers."""
    pass

class ProviderAuthError(ProviderError):
    """Exception raised when API keys are missing or invalid."""
    pass

class ProviderRateLimitError(ProviderError):
    """Exception raised when API rate limits are exceeded."""
    pass

class ProviderConnectionError(ProviderError):
    """Exception raised when network connections or timeouts fail."""
    pass

class ProviderAPIError(ProviderError):
    """Exception raised for general API errors (invalid inputs, internal failures)."""
    pass
