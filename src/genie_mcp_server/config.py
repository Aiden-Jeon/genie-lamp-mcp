"""Configuration management for Genie MCP Server."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabricksConfig(BaseSettings):
    """Databricks configuration from environment variables.

    Supports multiple authentication methods:
    1. Personal Access Token (DATABRICKS_TOKEN)
    2. OAuth M2M Service Principal (DATABRICKS_CLIENT_ID + SECRET)
    3. Default auth from Databricks CLI config
    """

    host: str  # Databricks workspace URL (e.g., https://your-workspace.cloud.databricks.com)
    token: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    timeout_seconds: int = 300
    poll_interval_seconds: int = 2
    max_retries: int = 3
    serving_endpoint_name: str = "databricks-dbrx-instruct"

    model_config = SettingsConfigDict(
        env_prefix="DATABRICKS_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


def get_databricks_config() -> DatabricksConfig:
    """Load and return Databricks configuration from environment variables."""
    return DatabricksConfig()
