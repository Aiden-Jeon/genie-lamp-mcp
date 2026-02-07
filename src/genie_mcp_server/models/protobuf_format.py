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
            "text_instructions": [{"id": "...", "content": ["line1\\n"]}],
            "join_specs": [{"left": {...}, "right": {...}, "sql": ["..."]}],
            "sql_snippets": {"expressions": [...], "measures": [...], "filters": [...]},
            "example_question_sqls": [{"id": "...", "question": ["..."], "sql": ["..."]}]
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

    # Build instructions section
    instructions_section: dict[str, Any] = {}

    # 1. Convert plain text instructions to text_instructions
    if config.instructions:
        content_lines = []

        # Add business context section
        content_lines.append("BUSINESS CONTEXT:\n")
        content_lines.append(f"{config.description}\n")
        content_lines.append(f"Purpose: {config.purpose}\n")
        content_lines.append("\n")

        # Add plain text instructions
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

        instructions_section["text_instructions"] = [{
            "id": generate_id(),
            "content": content_lines
        }]

    # 2. Convert join_specifications to join_specs
    if config.join_specifications:
        join_specs = []
        for join in config.join_specifications:
            # Parse table names to extract identifier and alias
            left_parts = join.left_table.split(".")
            right_parts = join.right_table.split(".")

            # Use last part as alias (table name)
            left_alias = left_parts[-1] if left_parts else "left_table"
            right_alias = right_parts[-1] if right_parts else "right_table"

            # Build SQL condition with join type prefix for non-INNER joins
            join_sql = join.join_condition
            if join.join_type and join.join_type.upper() != "INNER":
                join_sql = f"{join.join_type.upper()} JOIN: {join.join_condition}"

            join_spec = {
                "id": generate_id(),
                "left": {
                    "identifier": join.left_table,
                    "alias": left_alias
                },
                "right": {
                    "identifier": join.right_table,
                    "alias": right_alias
                },
                "sql": [join_sql]
            }

            # Build instruction array from description and/or instruction
            instruction_parts = []
            if join.description:
                instruction_parts.append(join.description)
            if join.instruction:
                instruction_parts.append(join.instruction)
            if instruction_parts:
                join_spec["instruction"] = instruction_parts

            join_specs.append(join_spec)

        instructions_section["join_specs"] = join_specs

    # 3. Convert sql_snippets to sql_snippets (with proper structure)
    if config.sql_snippets:
        sql_snippets_section: dict[str, list] = {}

        # Convert measures
        if config.sql_snippets.measures:
            measures = []
            for measure in config.sql_snippets.measures:
                measure_obj = {
                    "id": generate_id(),
                    "alias": measure.alias,
                    "sql": [measure.sql],  # Convert to array
                    "display_name": measure.display_name
                }
                if measure.synonyms:
                    measure_obj["synonyms"] = measure.synonyms
                if measure.instruction:
                    measure_obj["instruction"] = [measure.instruction]
                measures.append(measure_obj)
            sql_snippets_section["measures"] = measures

        # Convert expressions
        if config.sql_snippets.expressions:
            expressions = []
            for expr in config.sql_snippets.expressions:
                expr_obj = {
                    "id": generate_id(),
                    "alias": expr.alias,
                    "sql": [expr.sql],  # Convert to array
                    "display_name": expr.display_name
                }
                if expr.synonyms:
                    expr_obj["synonyms"] = expr.synonyms
                if expr.instruction:
                    expr_obj["instruction"] = [expr.instruction]
                expressions.append(expr_obj)
            sql_snippets_section["expressions"] = expressions

        # Convert filters
        if config.sql_snippets.filters:
            filters = []
            for filter_item in config.sql_snippets.filters:
                filter_obj = {
                    "id": generate_id(),
                    "sql": [filter_item.sql],  # Convert to array
                    "display_name": filter_item.display_name
                }
                if filter_item.synonyms:
                    filter_obj["synonyms"] = filter_item.synonyms
                filters.append(filter_obj)
            sql_snippets_section["filters"] = filters

        if sql_snippets_section:
            instructions_section["sql_snippets"] = sql_snippets_section

    # 4. Convert example_sql_queries to example_question_sqls
    if config.example_sql_queries:
        example_question_sqls = []
        for example in config.example_sql_queries:
            example_obj = {
                "id": generate_id(),
                "question": [example.question],
                "sql": [example.sql_query]  # Convert to array
            }
            # Note: description is not a valid protobuf field for example_question_sqls
            example_question_sqls.append(example_obj)

        instructions_section["example_question_sqls"] = example_question_sqls

    # Add instructions section if not empty
    if instructions_section:
        protobuf_format["instructions"] = instructions_section

    # Sort all arrays by 'id' field (Databricks API requires sorted entries)
    # Sort tables by identifier
    if "data_sources" in protobuf_format and "tables" in protobuf_format["data_sources"]:
        protobuf_format["data_sources"]["tables"].sort(key=lambda t: t.get("identifier", ""))

    # Sort sample_questions by id
    if "config" in protobuf_format and "sample_questions" in protobuf_format.get("config", {}):
        protobuf_format["config"]["sample_questions"].sort(key=lambda q: q.get("id", ""))

    # Sort instructions sub-sections by id
    instr = protobuf_format.get("instructions", {})
    for key in ["text_instructions", "join_specs", "example_question_sqls"]:
        if key in instr:
            instr[key].sort(key=lambda item: item.get("id", ""))

    # Sort sql_snippets sub-sections by id
    snippets = instr.get("sql_snippets", {})
    for key in ["measures", "expressions", "filters"]:
        if key in snippets:
            snippets[key].sort(key=lambda item: item.get("id", ""))

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

    # Extract join specifications
    join_specifications = []
    for join_spec in data.get("instructions", {}).get("join_specs", []):
        left_identifier = join_spec.get("left", {}).get("identifier", "")
        right_identifier = join_spec.get("right", {}).get("identifier", "")
        sql = join_spec.get("sql", [])
        join_condition = sql[0] if sql else ""

        if left_identifier and right_identifier and join_condition:
            join_obj = {
                "left_table": left_identifier,
                "right_table": right_identifier,
                "join_condition": join_condition,
                "join_type": join_spec.get("join_type", "INNER")
            }
            # instruction is stored as an array in protobuf format
            instruction_arr = join_spec.get("instruction", [])
            if isinstance(instruction_arr, str):
                instruction_arr = [instruction_arr]
            if instruction_arr:
                join_obj["instruction"] = " ".join(instruction_arr)
            join_specifications.append(join_obj)

    # Extract SQL snippets
    sql_snippets = {}
    snippets_section = data.get("instructions", {}).get("sql_snippets", {})

    # Extract measures
    measures = []
    for measure in snippets_section.get("measures", []):
        sql = measure.get("sql", [])
        measure_obj = {
            "alias": measure.get("alias", ""),
            "sql": sql[0] if sql else "",
            "display_name": measure.get("display_name", "")
        }
        if measure.get("synonyms"):
            measure_obj["synonyms"] = measure["synonyms"]
        if measure.get("instruction"):
            measure_obj["instruction"] = measure["instruction"]
        measures.append(measure_obj)

    # Extract expressions
    expressions = []
    for expr in snippets_section.get("expressions", []):
        sql = expr.get("sql", [])
        expr_obj = {
            "alias": expr.get("alias", ""),
            "sql": sql[0] if sql else "",
            "display_name": expr.get("display_name", "")
        }
        if expr.get("synonyms"):
            expr_obj["synonyms"] = expr["synonyms"]
        if expr.get("instruction"):
            expr_obj["instruction"] = expr["instruction"]
        expressions.append(expr_obj)

    # Extract filters
    filters = []
    for filter_item in snippets_section.get("filters", []):
        sql = filter_item.get("sql", [])
        filter_obj = {
            "sql": sql[0] if sql else "",
            "display_name": filter_item.get("display_name", "")
        }
        if filter_item.get("synonyms"):
            filter_obj["synonyms"] = filter_item["synonyms"]
        filters.append(filter_obj)

    if measures or expressions or filters:
        sql_snippets = {
            "measures": measures,
            "expressions": expressions,
            "filters": filters
        }

    # Extract example SQL queries
    example_sql_queries = []
    for example in data.get("instructions", {}).get("example_question_sqls", []):
        question = example.get("question", [])
        sql = example.get("sql", [])
        if question and sql:
            example_obj = {
                "question": question[0],
                "sql_query": sql[0]
            }
            if example.get("description"):
                example_obj["description"] = example["description"]
            example_sql_queries.append(example_obj)

    return GenieSpaceConfig(
        space_name="Imported Space",
        description="Imported from Databricks",
        purpose="Configuration imported from existing Genie space",
        tables=tables,
        instructions=instructions,
        benchmark_questions=benchmark_questions,
        join_specifications=join_specifications if join_specifications else None,
        sql_snippets=sql_snippets if sql_snippets else None,
        example_sql_queries=example_sql_queries if example_sql_queries else None
    )
