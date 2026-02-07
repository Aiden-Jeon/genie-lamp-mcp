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
    config_json: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    parent_path: Optional[str] = None,
) -> str:
    """Create a new Genie space from GenieSpaceConfig JSON.

    This is the final step in the configuration workflow:
    1. get_config_schema - Get JSON schema for validation
    2. get_config_template - Get domain-specific template (optional)
    3. validate_space_config - Validate your configuration
    4. create_genie_space - Create the space (THIS TOOL)

    Args:
        warehouse_id: SQL warehouse ID for query execution
        config_json: JSON string with GenieSpaceConfig (instructions, tables, examples, SQL snippets)
        title: Optional space title (defaults to config.space_name)
        description: Optional space description (defaults to config.description)
        parent_path: Optional parent path in workspace

    Returns:
        JSON string with created space details including space_id

    Example config_json:
        {
            "space_name": "Sales Analytics",
            "description": "Natural language querying for sales data",
            "purpose": "Enable business users to analyze sales trends",
            "tables": [
                {"catalog_name": "main", "schema_name": "sales", "table_name": "orders"}
            ],
            "instructions": [
                {"content": "When users ask about revenue, use SUM(amount)"}
            ],
            "example_sql_queries": [
                {"question": "What is total revenue?", "sql_query": "SELECT SUM(amount) FROM orders"}
            ],
            "benchmark_questions": [
                {"question": "What is total revenue last month?"}
            ]
        }
    """
    return space_tools.create_genie_space(
        warehouse_id=warehouse_id,
        config_json=config_json,
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
def get_genie_space(space_id: str, include_config: bool = False) -> str:
    """Get details of a specific Genie space.

    Args:
        space_id: Unique identifier for the space
        include_config: Whether to include full Protobuf configuration (serialized_space)

    Returns:
        JSON string with space details

    Note:
        When include_config=True, the serialized_space field contains Databricks Protobuf
        format with data_sources (tables), sample_questions, and text_instructions.
    """
    return space_tools.get_genie_space(space_id=space_id, include_config=include_config)


@mcp.tool()
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
        Use the same GenieSpaceConfig format as create_genie_space.
    """
    return space_tools.update_genie_space(
        space_id=space_id,
        config_json=config_json,
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
def get_config_schema() -> str:
    """Get the JSON schema and documentation for Genie space configurations.

    Returns complete schema with:
    - Field definitions and types
    - Required vs optional fields
    - Validation rules and scoring criteria
    - Best practices and guidelines
    - Complete example configuration
    - Usage notes and workflow

    Use this to understand how to generate valid Genie space configurations.
    This is the recommended approach for AI assistants to create configs.

    Workflow:
    1. Call this tool to get the schema
    2. Optionally call get_config_template() for a domain-specific starting point
    3. Generate config based on schema and user requirements
    4. Validate with validate_space_config()
    5. Create space with create_genie_space()

    Returns:
        JSON string with complete schema documentation
    """
    import json

    from genie_mcp_server.generators.schema_exporter import get_json_schema

    schema = get_json_schema()
    return json.dumps(schema, indent=2)


@mcp.tool()
def get_config_template(domain: str = "minimal") -> str:
    """Get a pre-configured config template for a specific domain.

    Returns a template with domain-appropriate metadata, instructions,
    example queries, and placeholders for customization.

    Available domains:
    - minimal: Bare minimum valid config (score ~70)
    - sales: Revenue tracking, transaction analysis, time-based metrics
    - customer: User behavior, segmentation, retention analysis
    - inventory: Stock levels, warehouse operations
    - financial: Budgets, expenses, P&L reporting
    - hr: Headcount, compensation, performance

    Placeholders to replace:
    - [CATALOG]: Your Unity Catalog name
    - [SCHEMA]: Your schema name
    - [TABLE_NAME]: Your table name

    After getting a template:
    1. Replace placeholders with actual values
    2. Customize instructions based on actual column names
    3. Validate with validate_space_config()
    4. Create space with create_genie_space()

    Args:
        domain: Type of analytics space (minimal/sales/customer/inventory/financial/hr)

    Returns:
        JSON string with template configuration
    """
    import json

    from genie_mcp_server.generators.templates import get_template

    # Validate domain parameter
    valid_domains = ["minimal", "sales", "customer", "inventory", "financial", "hr"]
    if domain not in valid_domains:
        return json.dumps(
            {
                "error": f"Invalid domain '{domain}'. Valid options: {', '.join(valid_domains)}",
                "valid_domains": valid_domains,
            }
        )

    template = get_template(domain)
    return json.dumps(template, indent=2)


@mcp.tool()
def generate_space_config(
    requirements: str,
    warehouse_id: str,
    catalog_name: str,
    serving_endpoint_name: Optional[str] = None,
    validate_sql: bool = True,
) -> str:
    """DEPRECATED: Generate a Genie space configuration from natural language requirements.

    ⚠️ This tool is deprecated because it requires an external serving endpoint.

    Instead, use the recommended workflow:
    1. get_config_schema() - Get schema and documentation
    2. get_config_template() - Get domain-specific template (optional)
    3. Generate config using AI assistant with schema guidance
    4. validate_space_config() - Validate before creating
    5. create_genie_space() - Create the space

    This approach:
    - Eliminates serving endpoint dependency
    - Zero additional costs
    - Faster generation (local)
    - More flexible customization
    - Better for AI assistants

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


# ============================================================================
# MCP Prompts (Skills)
# ============================================================================

from genie_mcp_server.skills import (
    create_space_skill,
    ask_skill,
    inspect_skill,
    bulk_skill,
)


@mcp.prompt()
def create_space(
    catalog_name: str,
    schema_name: str,
    table_names: str,
    warehouse_id: Optional[str] = None,
    domain: str = "minimal",
    space_name: Optional[str] = None,
    quick: bool = False,
    expert: bool = False,
) -> str:
    """Create a Genie space with guided workflow.

    Quick mode: Create with smart defaults (no validation feedback)
    Guided mode (default): Step-by-step with validation
    Expert mode: Return config for manual editing

    Example:
        catalog_name="main", schema_name="sales", table_names="orders,customers"
    """
    result = create_space_skill.run(
        catalog_name=catalog_name,
        schema_name=schema_name,
        table_names=table_names,
        warehouse_id=warehouse_id,
        domain=domain,
        space_name=space_name,
        quick=quick,
        expert=expert,
    )
    return result


@mcp.prompt()
def ask(
    question: str,
    space_id: Optional[str] = None,
    space_name: Optional[str] = None,
    new_conversation: bool = False,
    preview_only: bool = False,
    timeout: int = 300,
    verbose: bool = False,
) -> str:
    """Ask questions to Genie spaces with smart conversation tracking.

    Automatically continues conversations or starts new ones.

    Example:
        question="What is total revenue?", space_id="abc123"
    """
    result = ask_skill.run(
        question=question,
        space_id=space_id,
        space_name=space_name,
        new_conversation=new_conversation,
        preview_only=preview_only,
        timeout=timeout,
        verbose=verbose,
    )
    return result


@mcp.prompt()
def inspect(
    space_id: str,
    mode: str = "health",
    compare_with: Optional[str] = None,
    search_tables: Optional[str] = None,
    search_keywords: Optional[str] = None,
    output_file: Optional[str] = None,
) -> str:
    """Inspect space configuration and health.

    Modes:
    - health: Analyze config quality and activity
    - export: Extract config as JSON
    - diff: Compare two spaces
    - find: Search spaces by table/keyword

    Example:
        space_id="abc123", mode="health"
    """
    result = inspect_skill.run(
        space_id=space_id,
        mode=mode,
        compare_with=compare_with,
        search_tables=search_tables,
        search_keywords=search_keywords,
        output_file=output_file,
    )
    return result


@mcp.prompt()
def bulk(
    operation: str,
    space_ids: Optional[str] = None,
    pattern: Optional[str] = None,
    add_instructions: Optional[str] = None,
    add_tables: Optional[str] = None,
    dry_run: bool = True,
) -> str:
    """Bulk operations on multiple spaces.

    Operations:
    - update: Add instructions/tables to multiple spaces
    - delete: Delete spaces matching pattern
    - clone: Duplicate space with modifications

    Example:
        operation="update", space_ids="abc,def", add_instructions="Use fiscal year"
    """
    result = bulk_skill.run(
        operation=operation,
        space_ids=space_ids,
        pattern=pattern,
        add_instructions=add_instructions,
        add_tables=add_tables,
        dry_run=dry_run,
    )
    return result


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
