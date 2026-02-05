"""Configuration generation tools for MCP server."""

import json
from typing import Optional

from databricks.sdk import WorkspaceClient

from genie_mcp_server.generators.space_config_generator import GenieConfigGenerator
from genie_mcp_server.generators.validator import ConfigValidator
from genie_mcp_server.models.responses import TableMetadata

# Global instances - will be set by server.py
_workspace_client: Optional[WorkspaceClient] = None
_config_generator: Optional[GenieConfigGenerator] = None
_config_validator: Optional[ConfigValidator] = None


def set_workspace_client(client: WorkspaceClient, serving_endpoint_name: str) -> None:
    """Set the global workspace client and initialize generator.

    Args:
        client: WorkspaceClient instance
        serving_endpoint_name: Name of the serving endpoint for LLM calls
    """
    global _workspace_client, _config_generator, _config_validator
    _workspace_client = client
    _config_generator = GenieConfigGenerator(
        workspace_client=client, serving_endpoint_name=serving_endpoint_name
    )
    _config_validator = ConfigValidator()


def get_workspace_client() -> WorkspaceClient:
    """Get the global workspace client instance."""
    if _workspace_client is None:
        raise RuntimeError("Workspace client not initialized")
    return _workspace_client


def get_config_generator() -> GenieConfigGenerator:
    """Get the global config generator instance."""
    if _config_generator is None:
        raise RuntimeError("Config generator not initialized")
    return _config_generator


def get_config_validator() -> ConfigValidator:
    """Get the global config validator instance."""
    if _config_validator is None:
        raise RuntimeError("Config validator not initialized")
    return _config_validator


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
    generator = get_config_generator()
    validator = get_config_validator()

    # Generate configuration
    llm_response = generator.generate_config(
        requirements=requirements,
        catalog_name=catalog_name,
        warehouse_id=warehouse_id,
    )

    # Validate configuration
    config_dict = llm_response.genie_space_config.model_dump()
    validation_report = validator.validate_config(config_dict, validate_sql=validate_sql)

    # Build response
    result = {
        "genie_space_config": config_dict,
        "reasoning": llm_response.reasoning,
        "confidence_score": llm_response.confidence_score,
        "validation_report": {
            "valid": validation_report.valid,
            "errors": validation_report.errors,
            "warnings": validation_report.warnings,
            "score": validation_report.score,
        },
    }

    return json.dumps(result, indent=2)


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
    validator = get_config_validator()

    try:
        config_dict = json.loads(config)
    except json.JSONDecodeError as e:
        return json.dumps(
            {"valid": False, "errors": [f"Invalid JSON: {str(e)}"], "warnings": [], "score": 0},
            indent=2,
        )

    validation_report = validator.validate_config(config_dict, validate_sql=validate_sql)

    result = {
        "valid": validation_report.valid,
        "errors": validation_report.errors,
        "warnings": validation_report.warnings,
        "score": validation_report.score,
    }

    return json.dumps(result, indent=2)


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
    client = get_workspace_client()

    try:
        tables = []

        # List tables in schema
        table_list = client.tables.list(catalog_name=catalog_name, schema_name=schema_name)

        for table in table_list:
            # Filter by table names if provided
            if table_names and table.name not in table_names:
                continue

            # Get full table info
            table_info = client.tables.get(
                full_name=f"{catalog_name}.{schema_name}.{table.name}"
            )

            # Extract column information
            columns = []
            if hasattr(table_info, "columns") and table_info.columns:
                for col in table_info.columns:
                    columns.append(
                        {
                            "name": col.name,
                            "type": getattr(col, "type_text", getattr(col, "type_name", "UNKNOWN")),
                            "comment": getattr(col, "comment", None),
                        }
                    )

            metadata = TableMetadata(
                catalog_name=catalog_name,
                schema_name=schema_name,
                table_name=table.name,
                table_type=getattr(table, "table_type", None),
                comment=getattr(table_info, "comment", None),
                columns=columns,
                owner=getattr(table_info, "owner", None),
            )

            tables.append(metadata.model_dump())

        result = {"catalog_name": catalog_name, "schema_name": schema_name, "tables": tables}

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Failed to extract table metadata: {str(e)}"}, indent=2)
