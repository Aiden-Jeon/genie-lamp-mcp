"""Databricks Genie API client wrapper."""

import json
from typing import Any, Optional

from databricks.sdk import WorkspaceClient

from genie_mcp_server.models.protobuf_format import config_to_protobuf
from genie_mcp_server.models.space import GenieSpaceConfig
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
        config: GenieSpaceConfig,
        title: Optional[str] = None,
        description: Optional[str] = None,
        parent_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new Genie space with AI configuration.

        Args:
            warehouse_id: SQL warehouse ID for query execution
            config: Genie space configuration (instructions, tables, examples, etc.)
            title: Optional space title (defaults to config.space_name)
            description: Optional space description (defaults to config.description)
            parent_path: Optional parent path in workspace

        Returns:
            Dictionary with created space details

        Raises:
            GenieError: If space creation fails

        Note:
            The config is automatically converted to Databricks Protobuf format (version 2)
            before being sent to the API. This format includes data_sources, sample_questions,
            and text_instructions.
        """
        try:
            # Convert our user-friendly config to Databricks Protobuf format
            serialized_space = config_to_protobuf(config)

            # Use config values as defaults if not explicitly provided
            if title is None:
                title = config.space_name
            if description is None:
                description = config.description

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

    def get_space(
        self, space_id: str, include_serialized_space: bool = False
    ) -> dict[str, Any]:
        """Get details of a specific Genie space.

        Args:
            space_id: Space identifier
            include_serialized_space: Whether to include the full Protobuf configuration

        Returns:
            Dictionary with space details

        Raises:
            GenieError: If space not found or retrieval fails
        """
        try:
            space = self.genie.get_space(
                space_id=space_id, include_serialized_space=include_serialized_space
            )

            result = {
                "space_id": space.space_id,
                "title": space.title,
                "description": space.description,
                "warehouse_id": space.warehouse_id,
                "owner_user_id": getattr(space, "owner_user_id", None),
                "created_timestamp": getattr(space, "created_timestamp", None),
                "updated_timestamp": getattr(space, "updated_timestamp", None),
            }

            if include_serialized_space:
                result["serialized_space"] = space.serialized_space

            return result
        except Exception as e:
            raise translate_databricks_error(e)

    def update_space(
        self,
        space_id: str,
        config: Optional[GenieSpaceConfig] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        warehouse_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update an existing Genie space.

        Args:
            space_id: Space identifier
            config: Optional new Genie space configuration
            title: Optional new title
            description: Optional new description
            warehouse_id: Optional new warehouse ID

        Returns:
            Dictionary with updated space details

        Raises:
            GenieError: If space not found or update fails

        Note:
            If config is provided, it will be converted to Databricks Protobuf format.
        """
        try:
            serialized_space = None
            if config:
                serialized_space = config_to_protobuf(config)

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
            self.genie.trash_space(space_id=space_id)
            return {"status": "success", "message": f"Space {space_id} deleted successfully"}
        except Exception as e:
            raise translate_databricks_error(e)
