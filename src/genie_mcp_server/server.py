"""Main MCP server for Databricks Genie."""

from typing import Optional

from fastmcp import FastMCP

from genie_mcp_server.auth import create_workspace_client
from genie_mcp_server.client.genie_client import GenieClient
from genie_mcp_server.config import get_databricks_config
from genie_mcp_server.tools import config_gen_tools, conversation_tools, space_tools

# Initialize fastmcp server
mcp = FastMCP("genie-mcp-server")

# Global clients (initialized on startup)
workspace_client = None
genie_client = None


@mcp.tool()
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
    return space_tools.create_genie_space(
        warehouse_id=warehouse_id,
        serialized_space=serialized_space,
        title=title,
        description=description,
        parent_path=parent_path,
    )


@mcp.tool()
def list_genie_spaces(page_size: Optional[int] = None, page_token: Optional[str] = None) -> str:
    """List all Genie spaces in the workspace.

    Args:
        page_size: Number of spaces to return per page (default: all)
        page_token: Token for pagination to get next page

    Returns:
        JSON string with array of space summaries and optional next_page_token
    """
    return space_tools.list_genie_spaces(page_size=page_size, page_token=page_token)


@mcp.tool()
def get_genie_space(space_id: str, include_config: bool = True) -> str:
    """Get details of a specific Genie space.

    Args:
        space_id: Unique identifier for the space
        include_config: Whether to include full configuration (serialized_space)

    Returns:
        JSON string with space details including configuration if requested
    """
    return space_tools.get_genie_space(space_id=space_id, include_config=include_config)


@mcp.tool()
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
    return space_tools.update_genie_space(
        space_id=space_id,
        serialized_space=serialized_space,
        title=title,
        description=description,
        warehouse_id=warehouse_id,
    )


@mcp.tool()
def delete_genie_space(space_id: str) -> str:
    """Delete a Genie space (soft delete - moves to trash).

    Args:
        space_id: Unique identifier for the space to delete

    Returns:
        JSON string with success confirmation
    """
    return space_tools.delete_genie_space(space_id=space_id)


@mcp.tool()
async def ask_genie(
    space_id: str,
    question: str,
    timeout_seconds: int = 300,
    poll_interval_seconds: int = 2,
) -> str:
    """Ask a question to Genie and wait for the response.

    This tool applies rate limiting (5 queries per minute) and polls until
    the query completes or times out.

    Args:
        space_id: Unique identifier for the Genie space
        question: Natural language question to ask
        timeout_seconds: Maximum time to wait for response (default: 300)
        poll_interval_seconds: Time between status checks (default: 2)

    Returns:
        JSON string with conversation_id, message_id, status, response_text,
        sql_query, and query_results if available
    """
    return await conversation_tools.ask_genie(
        space_id=space_id,
        question=question,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )


@mcp.tool()
async def continue_conversation(
    space_id: str,
    conversation_id: str,
    question: str,
    timeout_seconds: int = 300,
    poll_interval_seconds: int = 2,
) -> str:
    """Continue an existing conversation with a follow-up question.

    Args:
        space_id: Unique identifier for the Genie space
        conversation_id: ID of the conversation to continue
        question: Follow-up question
        timeout_seconds: Maximum time to wait for response (default: 300)
        poll_interval_seconds: Time between status checks (default: 2)

    Returns:
        JSON string with message details and results
    """
    return await conversation_tools.continue_conversation(
        space_id=space_id,
        conversation_id=conversation_id,
        question=question,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )


@mcp.tool()
def get_query_results(
    space_id: str, conversation_id: str, message_id: str, attachment_id: Optional[str] = None
) -> str:
    """Fetch query result data from a completed message.

    Args:
        space_id: Unique identifier for the Genie space
        conversation_id: ID of the conversation
        message_id: ID of the message with query results
        attachment_id: Optional specific attachment ID

    Returns:
        JSON string with query results (up to 5,000 rows)
    """
    return conversation_tools.get_query_results(
        space_id=space_id,
        conversation_id=conversation_id,
        message_id=message_id,
        attachment_id=attachment_id,
    )


@mcp.tool()
def list_conversations(
    space_id: str, page_size: int = 50, page_token: Optional[str] = None
) -> str:
    """List conversations in a Genie space.

    Args:
        space_id: Unique identifier for the Genie space
        page_size: Number of conversations to return (default: 50)
        page_token: Token for pagination

    Returns:
        JSON string with conversation summaries
    """
    return conversation_tools.list_conversations(
        space_id=space_id, page_size=page_size, page_token=page_token
    )


@mcp.tool()
def get_conversation_history(space_id: str, conversation_id: str) -> str:
    """Get all messages in a conversation.

    Args:
        space_id: Unique identifier for the Genie space
        conversation_id: ID of the conversation

    Returns:
        JSON string with complete conversation thread
    """
    return conversation_tools.get_conversation_history(
        space_id=space_id, conversation_id=conversation_id
    )


@mcp.tool()
def generate_space_config(
    requirements: str,
    warehouse_id: str,
    catalog_name: str,
    serving_endpoint_name: Optional[str] = None,
    validate_sql: bool = True,
) -> str:
    """Generate a Genie space configuration from natural language requirements.

    This tool uses an LLM to generate a complete Genie space configuration based on
    your requirements. The generated configuration is validated before being returned.

    Args:
        requirements: Natural language description of desired Genie space
        warehouse_id: SQL warehouse ID for query execution
        catalog_name: Unity Catalog name to use
        serving_endpoint_name: Optional serving endpoint name (uses default if not provided)
        validate_sql: Whether to validate SQL syntax (default: True)

    Returns:
        JSON string with generated configuration, reasoning, confidence score,
        validation report, and warnings
    """
    return config_gen_tools.generate_space_config(
        requirements=requirements,
        warehouse_id=warehouse_id,
        catalog_name=catalog_name,
        serving_endpoint_name=serving_endpoint_name,
        validate_sql=validate_sql,
    )


@mcp.tool()
def validate_space_config(
    config: str, validate_sql: bool = True, catalog_name: Optional[str] = None
) -> str:
    """Validate a Genie space configuration.

    Performs multi-layer validation:
    - Schema validation (Pydantic model)
    - SQL syntax validation (if enabled)
    - Instruction quality scoring
    - Completeness check

    Args:
        config: JSON string containing Genie space configuration
        validate_sql: Whether to validate SQL syntax (default: True)
        catalog_name: Optional catalog name for context

    Returns:
        JSON string with validation results including errors, warnings, and quality score
    """
    return config_gen_tools.validate_space_config(
        config=config, validate_sql=validate_sql, catalog_name=catalog_name
    )


@mcp.tool()
def extract_table_metadata(
    catalog_name: str, schema_name: str, table_names: Optional[list[str]] = None
) -> str:
    """Extract metadata for Unity Catalog tables.

    Queries Unity Catalog to get table schemas, column information, and descriptions.
    This metadata can be used as context for configuration generation.

    Args:
        catalog_name: Catalog name in Unity Catalog
        schema_name: Schema name in Unity Catalog
        table_names: Optional list of specific table names to include (default: all tables in schema)

    Returns:
        JSON string with table metadata including columns, types, and descriptions
    """
    return config_gen_tools.extract_table_metadata(
        catalog_name=catalog_name, schema_name=schema_name, table_names=table_names
    )


def main():
    """Main entry point for the MCP server."""
    global workspace_client, genie_client

    # Load configuration
    config = get_databricks_config()

    # Create authenticated workspace client
    workspace_client = create_workspace_client(config)

    # Initialize Genie client
    genie_client = GenieClient(workspace_client)

    # Set clients in tool modules
    space_tools.set_genie_client(genie_client)
    conversation_tools.set_workspace_client(workspace_client)
    config_gen_tools.set_workspace_client(workspace_client, config.serving_endpoint_name)

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
