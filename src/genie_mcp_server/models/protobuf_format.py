"""Transformer for converting GenieSpaceConfig to Databricks Protobuf format.

The Databricks Genie API expects serialized_space to be in a specific Protobuf-compatible
JSON format (version 2). This module provides transformation between our user-friendly
GenieSpaceConfig model and the API's expected format.
"""

import json
import uuid
from typing import Any

from genie_mcp_server.models.space import GenieSpaceConfig


def generate_id() -> str:
    """Generate a unique ID in the format expected by Databricks.

    Returns:
        32-character hexadecimal string (UUID without hyphens)
    """
    return uuid.uuid4().hex


def config_to_protobuf(config: GenieSpaceConfig) -> str:
    """Convert GenieSpaceConfig to Databricks Protobuf JSON format.

    Args:
        config: User-friendly Genie space configuration

    Returns:
        JSON string in Databricks Protobuf format (version 2)

    Format structure:
    {
        "version": 2,
        "data_sources": {
            "tables": [{"identifier": "catalog.schema.table"}]
        },
        "config": {
            "sample_questions": [{"id": "...", "question": ["..."]}]
        },
        "instructions": {
            "text_instructions": [{"id": "...", "content": ["line1\\n", "line2\\n"]}]
        }
    }
    """
    protobuf_format: dict[str, Any] = {
        "version": 2,
        "data_sources": {
            "tables": []
        }
    }

    # Convert tables to identifiers
    for table in config.tables:
        identifier = f"{table.catalog_name}.{table.schema_name}.{table.table_name}"
        protobuf_format["data_sources"]["tables"].append({
            "identifier": identifier
        })

    # Convert sample questions (from example_sql_queries and benchmark_questions)
    sample_questions = []

    # Add example SQL queries as sample questions
    for example in config.example_sql_queries:
        sample_questions.append({
            "id": generate_id(),
            "question": [example.question]
        })

    # Add benchmark questions
    for benchmark in config.benchmark_questions:
        sample_questions.append({
            "id": generate_id(),
            "question": [benchmark.question]
        })

    if sample_questions:
        protobuf_format["config"] = {
            "sample_questions": sample_questions
        }

    # Convert instructions to text_instructions format
    text_instructions = []

    # Combine all instructions into a single comprehensive instruction
    if config.instructions or config.example_sql_queries or config.sql_snippets or config.join_specifications:
        content_lines = []

        # Add business context section
        content_lines.append("BUSINESS CONTEXT:\n")
        content_lines.append(f"{config.description}\n")
        content_lines.append(f"Purpose: {config.purpose}\n")
        content_lines.append("\n")

        # Add plain text instructions
        if config.instructions:
            content_lines.append("INSTRUCTIONS:\n")
            for idx, instruction in enumerate(config.instructions, 1):
                priority_marker = f" [Priority: {instruction.priority}]" if instruction.priority else ""
                content_lines.append(f"{idx}. {instruction.content}{priority_marker}\n")
            content_lines.append("\n")

        # Add table information
        if config.tables:
            content_lines.append("DATA SOURCES:\n")
            for table in config.tables:
                identifier = f"{table.catalog_name}.{table.schema_name}.{table.table_name}"
                desc = f" - {table.description}" if table.description else ""
                content_lines.append(f"- {identifier}{desc}\n")
            content_lines.append("\n")

        # Add join specifications
        if config.join_specifications:
            content_lines.append("TABLE RELATIONSHIPS:\n")
            for join in config.join_specifications:
                content_lines.append(f"- {join.left_table} {join.join_type} JOIN {join.right_table}\n")
                content_lines.append(f"  ON {join.join_condition}\n")
                if join.description:
                    content_lines.append(f"  Description: {join.description}\n")
                if join.instruction:
                    content_lines.append(f"  Usage: {join.instruction}\n")
            content_lines.append("\n")

        # Add SQL snippets
        if config.sql_snippets:
            if config.sql_snippets.measures:
                content_lines.append("MEASURES (Aggregations):\n")
                for measure in config.sql_snippets.measures:
                    synonyms = f" (Synonyms: {', '.join(measure.synonyms)})" if measure.synonyms else ""
                    content_lines.append(f"- {measure.display_name}{synonyms}\n")
                    content_lines.append(f"  SQL: {measure.sql}\n")
                    if measure.instruction:
                        content_lines.append(f"  Usage: {measure.instruction}\n")
                content_lines.append("\n")

            if config.sql_snippets.expressions:
                content_lines.append("EXPRESSIONS (Dimensions/Calculated Fields):\n")
                for expr in config.sql_snippets.expressions:
                    synonyms = f" (Synonyms: {', '.join(expr.synonyms)})" if expr.synonyms else ""
                    content_lines.append(f"- {expr.display_name}{synonyms}\n")
                    content_lines.append(f"  SQL: {expr.sql}\n")
                    if expr.instruction:
                        content_lines.append(f"  Usage: {expr.instruction}\n")
                content_lines.append("\n")

            if config.sql_snippets.filters:
                content_lines.append("FILTERS (WHERE Conditions):\n")
                for filter in config.sql_snippets.filters:
                    synonyms = f" (Synonyms: {', '.join(filter.synonyms)})" if filter.synonyms else ""
                    content_lines.append(f"- {filter.display_name}{synonyms}\n")
                    content_lines.append(f"  SQL: {filter.sql}\n")
                content_lines.append("\n")

        # Add example SQL queries
        if config.example_sql_queries:
            content_lines.append("EXAMPLE QUERIES:\n")
            for idx, example in enumerate(config.example_sql_queries, 1):
                content_lines.append(f"{idx}. Question: {example.question}\n")
                content_lines.append(f"   SQL: {example.sql_query}\n")
                if example.description:
                    content_lines.append(f"   Note: {example.description}\n")
            content_lines.append("\n")

        text_instructions.append({
            "id": generate_id(),
            "content": content_lines
        })

    if text_instructions:
        protobuf_format["instructions"] = {
            "text_instructions": text_instructions
        }

    return json.dumps(protobuf_format)


def protobuf_to_config(protobuf_json: str) -> GenieSpaceConfig:
    """Convert Databricks Protobuf JSON format to GenieSpaceConfig.

    Args:
        protobuf_json: JSON string in Databricks Protobuf format

    Returns:
        User-friendly Genie space configuration

    Note:
        This is a best-effort conversion. Some information may be lost or
        simplified during the round-trip conversion since the formats are not
        perfectly symmetrical.
    """
    data = json.loads(protobuf_json)

    # Extract tables
    tables = []
    for table_ref in data.get("data_sources", {}).get("tables", []):
        identifier = table_ref.get("identifier", "")
        parts = identifier.split(".")
        if len(parts) == 3:
            tables.append({
                "catalog_name": parts[0],
                "schema_name": parts[1],
                "table_name": parts[2]
            })

    # Extract sample questions as benchmark questions
    benchmark_questions = []
    for sq in data.get("config", {}).get("sample_questions", []):
        questions = sq.get("question", [])
        if questions:
            benchmark_questions.append({
                "question": questions[0]  # Take first question variant
            })

    # Extract text instructions (simplified - just concatenate content)
    instructions = []
    for ti in data.get("instructions", {}).get("text_instructions", []):
        content = "".join(ti.get("content", []))
        if content:
            instructions.append({
                "content": content.strip()
            })

    return GenieSpaceConfig(
        space_name="Imported Space",
        description="Imported from Databricks",
        purpose="Configuration imported from existing Genie space",
        tables=tables,
        instructions=instructions,
        benchmark_questions=benchmark_questions
    )
