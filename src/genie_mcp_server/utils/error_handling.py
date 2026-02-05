"""Error handling and custom exceptions for Genie MCP Server."""


class GenieError(Exception):
    """Base exception for all Genie-related errors."""

    pass


class AuthenticationError(GenieError):
    """Authentication with Databricks failed."""

    pass


class SpaceNotFoundError(GenieError):
    """Requested Genie space does not exist."""

    pass


class RateLimitError(GenieError):
    """Rate limit exceeded for Genie API calls."""

    pass


class ValidationError(GenieError):
    """Configuration validation failed."""

    pass


class LLMError(GenieError):
    """Error calling LLM for config generation."""

    pass


class TimeoutError(GenieError):
    """Operation timed out."""

    pass


def translate_databricks_error(error: Exception) -> GenieError:
    """Translate Databricks SDK errors to user-friendly Genie errors.

    Args:
        error: Original exception from Databricks SDK

    Returns:
        Translated GenieError with actionable message
    """
    error_msg = str(error).lower()

    if "authentication" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
        return AuthenticationError(
            f"Authentication failed: {error}. "
            "Check DATABRICKS_TOKEN or DATABRICKS_CLIENT_ID/SECRET in your .env file."
        )
    elif "not found" in error_msg or "404" in error_msg:
        return SpaceNotFoundError(f"Resource not found: {error}")
    elif "rate limit" in error_msg or "429" in error_msg:
        return RateLimitError(
            f"Rate limit exceeded: {error}. "
            "Genie API allows 5 queries per minute in Public Preview."
        )
    elif "timeout" in error_msg:
        return TimeoutError(f"Operation timed out: {error}")
    else:
        return GenieError(f"Databricks API error: {error}")
