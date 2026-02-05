"""Genie space management tools for MCP server."""

import json
from typing import Optional

from genie_mcp_server.client.genie_client import GenieClient

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
    serialized_space: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    parent_path: Optional[str] = None,
) -> str:
    """Create a new Genie space from JSON configuration.

    Args:
        warehouse_id: SQL warehouse ID for query execution
        serialized_space: JSON string containing space configuration
        title: Optional space title
        description: Optional space description
        parent_path: Optional parent path in workspace

    Returns:
        JSON string with created space details including space_id
    """
    client = get_genie_client()
    result = client.create_space(
        warehouse_id=warehouse_id,
        serialized_space=serialized_space,
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


def get_genie_space(space_id: str, include_config: bool = True) -> str:
    """Get details of a specific Genie space.

    Args:
        space_id: Unique identifier for the space
        include_config: Whether to include full configuration (serialized_space)

    Returns:
        JSON string with space details including configuration if requested
    """
    client = get_genie_client()
    result = client.get_space(space_id=space_id)

    if not include_config:
        # Remove serialized_space from response
        result.pop("serialized_space", None)

    return json.dumps(result, indent=2)


def update_genie_space(
    space_id: str,
    serialized_space: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    warehouse_id: Optional[str] = None,
) -> str:
    """Update an existing Genie space.

    Args:
        space_id: Unique identifier for the space
        serialized_space: Optional new JSON configuration
        title: Optional new title
        description: Optional new description
        warehouse_id: Optional new SQL warehouse ID

    Returns:
        JSON string with updated space details
    """
    client = get_genie_client()
    result = client.update_space(
        space_id=space_id,
        serialized_space=serialized_space,
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
