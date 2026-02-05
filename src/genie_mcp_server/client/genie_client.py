"""Databricks Genie API client wrapper."""

import json
from typing import Any, Optional

from databricks.sdk import WorkspaceClient

from genie_mcp_server.utils.error_handling import translate_databricks_error


class GenieClient:
    """Wrapper around Databricks SDK for Genie API operations."""

    def __init__(self, workspace_client: WorkspaceClient):
        """Initialize Genie client.

        Args:
            workspace_client: Authenticated Databricks workspace client
        """
        self.client = workspace_client
        self.genie = workspace_client.genie

    def create_space(
        self,
        warehouse_id: str,
        serialized_space: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        parent_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new Genie space.

        Args:
            warehouse_id: SQL warehouse ID for query execution
            serialized_space: JSON string containing space configuration
            title: Optional space title
            description: Optional space description
            parent_path: Optional parent path in workspace

        Returns:
            Dictionary with created space details

        Raises:
            GenieError: If space creation fails
        """
        try:
            # Validate that serialized_space is valid JSON
            json.loads(serialized_space)

            space = self.genie.create_space(
                warehouse_id=warehouse_id,
                serialized_space=serialized_space,
                title=title,
                description=description,
            )

            return {
                "space_id": space.space_id,
                "title": space.title,
                "description": space.description,
                "warehouse_id": space.warehouse_id,
                "owner_user_id": getattr(space, "owner_user_id", None),
                "created_timestamp": getattr(space, "created_timestamp", None),
            }
        except Exception as e:
            raise translate_databricks_error(e)

    def list_spaces(
        self, page_size: Optional[int] = None, page_token: Optional[str] = None
    ) -> dict[str, Any]:
        """List all Genie spaces.

        Args:
            page_size: Number of spaces to return per page
            page_token: Token for pagination

        Returns:
            Dictionary with spaces array and optional next_page_token

        Raises:
            GenieError: If listing fails
        """
        try:
            result = self.genie.list_spaces(page_size=page_size, page_token=page_token)

            spaces = []
            for space in result.spaces or []:
                spaces.append(
                    {
                        "space_id": space.space_id,
                        "title": space.title,
                        "description": space.description,
                        "warehouse_id": space.warehouse_id,
                    }
                )

            return {"spaces": spaces, "next_page_token": result.next_page_token}
        except Exception as e:
            raise translate_databricks_error(e)

    def get_space(self, space_id: str) -> dict[str, Any]:
        """Get details of a specific Genie space.

        Args:
            space_id: Space identifier

        Returns:
            Dictionary with space details

        Raises:
            GenieError: If space not found or retrieval fails
        """
        try:
            space = self.genie.get_space(space_id=space_id)

            return {
                "space_id": space.space_id,
                "title": space.title,
                "description": space.description,
                "warehouse_id": space.warehouse_id,
                "serialized_space": space.serialized_space,
                "owner_user_id": getattr(space, "owner_user_id", None),
                "created_timestamp": getattr(space, "created_timestamp", None),
                "updated_timestamp": getattr(space, "updated_timestamp", None),
            }
        except Exception as e:
            raise translate_databricks_error(e)

    def update_space(
        self,
        space_id: str,
        serialized_space: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        warehouse_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update an existing Genie space.

        Args:
            space_id: Space identifier
            serialized_space: Optional new JSON configuration
            title: Optional new title
            description: Optional new description
            warehouse_id: Optional new warehouse ID

        Returns:
            Dictionary with updated space details

        Raises:
            GenieError: If space not found or update fails
        """
        try:
            if serialized_space:
                # Validate JSON
                json.loads(serialized_space)

            space = self.genie.update_space(
                space_id=space_id,
                serialized_space=serialized_space,
                title=title,
                description=description,
                warehouse_id=warehouse_id,
            )

            return {
                "space_id": space.space_id,
                "title": space.title,
                "description": space.description,
                "warehouse_id": space.warehouse_id,
                "updated_timestamp": getattr(space, "updated_timestamp", None),
            }
        except Exception as e:
            raise translate_databricks_error(e)

    def delete_space(self, space_id: str) -> dict[str, str]:
        """Delete a Genie space (soft delete - moves to trash).

        Args:
            space_id: Space identifier

        Returns:
            Dictionary with success message

        Raises:
            GenieError: If space not found or deletion fails
        """
        try:
            self.genie.delete_space(space_id=space_id)
            return {"status": "success", "message": f"Space {space_id} deleted successfully"}
        except Exception as e:
            raise translate_databricks_error(e)
