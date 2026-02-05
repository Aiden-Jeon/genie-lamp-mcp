"""Databricks authentication utilities."""

from databricks.sdk import WorkspaceClient

from genie_mcp_server.config import DatabricksConfig


def create_workspace_client(config: DatabricksConfig) -> WorkspaceClient:
    """Create authenticated Databricks workspace client.

    Authentication priority order:
    1. Personal Access Token (if config.token is set)
    2. OAuth M2M Service Principal (if config.client_id and client_secret are set)
    3. Default auth from Databricks CLI config

    Args:
        config: Databricks configuration with authentication credentials

    Returns:
        Authenticated WorkspaceClient instance
    """
    if config.token:
        return WorkspaceClient(host=config.host, token=config.token)
    elif config.client_id and config.client_secret:
        return WorkspaceClient(
            host=config.host,
            client_id=config.client_id,
            client_secret=config.client_secret,
        )
    else:
        # Use default auth (Databricks CLI config)
        return WorkspaceClient(host=config.host)
