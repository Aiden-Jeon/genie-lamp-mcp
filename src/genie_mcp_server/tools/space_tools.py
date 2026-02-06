"""Genie space management tools for MCP server."""

import json
from typing import Optional

from genie_mcp_server.client.genie_client import GenieClient
from genie_mcp_server.models.space import GenieSpaceConfig

# Global client instance - will be set by server.py
_genie_client: Optional[GenieClient] = None


def set_genie_client(client: GenieClient) -> None:
    """Set the global Genie client instance.

    Args:
        client: GenieClient instance to use for all tool operations
    """
    global _genie_client
    _genie_client = client


def get_genie_client() -> GenieClient:
    """Get the global Genie client instance.

    Returns:
        GenieClient instance

    Raises:
        RuntimeError: If client not initialized
    """
    if _genie_client is None:
        raise RuntimeError("Genie client not initialized. Call set_genie_client first.")
    return _genie_client


def create_genie_space(
    warehouse_id: str,
    config_json: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    parent_path: Optional[str] = None,
) -> str:
    """Create a new Genie space from GenieSpaceConfig JSON.

    Args:
        warehouse_id: SQL warehouse ID for query execution
        config_json: JSON string containing GenieSpaceConfig (instructions, tables, examples, etc.)
        title: Optional space title (defaults to config.space_name)
        description: Optional space description (defaults to config.description)
        parent_path: Optional parent path in workspace

    Returns:
        JSON string with created space details including space_id

    Note:
        The config is automatically converted to Databricks Protobuf format internally.
        Use the generate_space_config or get_config_template tools to create valid configs.
    """
    client = get_genie_client()

    # Parse the config JSON into a Pydantic model
    config_dict = json.loads(config_json)
    config = GenieSpaceConfig(**config_dict)

    result = client.create_space(
        warehouse_id=warehouse_id,
        config=config,
        title=title,
        description=description,
        parent_path=parent_path,
    )
    return json.dumps(result, indent=2)


def list_genie_spaces(page_size: Optional[int] = None, page_token: Optional[str] = None) -> str:
    """List all Genie spaces in the workspace.

    Args:
        page_size: Number of spaces to return per page (default: all)
        page_token: Token for pagination to get next page

    Returns:
        JSON string with array of space summaries and optional next_page_token
    """
    client = get_genie_client()
    result = client.list_spaces(page_size=page_size, page_token=page_token)
    return json.dumps(result, indent=2)


def get_genie_space(space_id: str, include_config: bool = False) -> str:
    """Get details of a specific Genie space.

    Args:
        space_id: Unique identifier for the space
        include_config: Whether to include full Protobuf configuration (serialized_space)

    Returns:
        JSON string with space details including configuration if requested

    Note:
        The serialized_space field (when included) contains the Databricks Protobuf format
        with data_sources, sample_questions, and text_instructions.
    """
    client = get_genie_client()
    result = client.get_space(space_id=space_id, include_serialized_space=include_config)
    return json.dumps(result, indent=2)


def update_genie_space(
    space_id: str,
    config_json: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    warehouse_id: Optional[str] = None,
) -> str:
    """Update an existing Genie space.

    Args:
        space_id: Unique identifier for the space
        config_json: Optional new GenieSpaceConfig as JSON string
        title: Optional new title
        description: Optional new description
        warehouse_id: Optional new SQL warehouse ID

    Returns:
        JSON string with updated space details

    Note:
        If config_json is provided, it will be automatically converted to Databricks
        Protobuf format internally.
    """
    client = get_genie_client()

    config = None
    if config_json:
        config_dict = json.loads(config_json)
        config = GenieSpaceConfig(**config_dict)

    result = client.update_space(
        space_id=space_id,
        config=config,
        title=title,
        description=description,
        warehouse_id=warehouse_id,
    )
    return json.dumps(result, indent=2)


def delete_genie_space(space_id: str) -> str:
    """Delete a Genie space (soft delete - moves to trash).

    Args:
        space_id: Unique identifier for the space to delete

    Returns:
        JSON string with success confirmation
    """
    client = get_genie_client()
    result = client.delete_space(space_id=space_id)
    return json.dumps(result, indent=2)
