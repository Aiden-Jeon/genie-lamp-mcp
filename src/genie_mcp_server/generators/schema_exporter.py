"""Export Pydantic schema as JSON Schema for AI assistants."""

from pydantic import TypeAdapter

from genie_mcp_server.generators.prompts import BEST_PRACTICES
from genie_mcp_server.models.space import GenieSpaceConfig


def get_json_schema() -> dict:
    """Export GenieSpaceConfig as JSON Schema for AI assistants.

    Returns a comprehensive schema document including:
    - Full JSON Schema from Pydantic model
    - Best practices and guidelines
    - Validation rules and scoring criteria
    - Complete example configuration

    This schema can be used by AI assistants to understand how to
    generate valid Genie space configurations.
    """
    # Export Pydantic model as JSON Schema
    adapter = TypeAdapter(GenieSpaceConfig)
    schema = adapter.json_schema()

    # Add custom metadata for AI assistants
    schema["best_practices"] = BEST_PRACTICES

    schema["validation_rules"] = {
        "required_fields": [
            "space_name",
            "description",
            "purpose",
            "tables (at least 1 table)",
        ],
        "recommended_fields": {
            "instructions": "Highly recommended for score >80. Provides guidance on how to query the data.",
            "example_sql_queries": "Highly recommended for score >80. Shows example queries for common questions.",
            "sql_snippets": "Optional. Defines reusable filters, expressions, and measures.",
            "join_specifications": "Required when using multiple tables. Defines how tables relate.",
            "benchmark_questions": "Optional. Used for testing the space quality.",
        },
        "minimum_requirements": {
            "tables": "At least 1 table required",
            "instructions": "Recommended: at least 3-5 specific instructions",
            "example_queries": "Recommended: at least 3-5 example queries",
        },
        "quality_scoring": {
            "90-100": "Excellent - Complete config with instructions, examples, and snippets",
            "80-89": "Good - Has instructions and examples, may be missing snippets",
            "70-79": "Acceptable - Basic config with tables and minimal guidance",
            "60-69": "Needs improvement - Missing key fields or insufficient detail",
            "0-59": "Poor - Incomplete or invalid configuration",
        },
    }

    # Include the complete example from the model
    example = GenieSpaceConfig.model_config.get("json_schema_extra", {}).get("examples", [{}])[
        0
    ]
    schema["example"] = example

    schema["usage_notes"] = {
        "workflow": [
            "1. Get this schema using get_config_schema() tool",
            "2. Optionally get a template using get_config_template() tool",
            "3. Generate config based on schema and user requirements",
            "4. Validate config using validate_space_config() tool",
            "5. Create space using create_genie_space() tool",
        ],
        "tips": [
            "Use specific column names in instructions (e.g., `event_date`, `user_id`)",
            "Format instructions with markdown for better readability",
            "Provide realistic example SQL queries that use actual table/column names",
            "Set instruction priorities (1=highest) for critical guidance",
            "Use fully qualified table names in join_specifications: catalog.schema.table",
        ],
    }

    return schema
