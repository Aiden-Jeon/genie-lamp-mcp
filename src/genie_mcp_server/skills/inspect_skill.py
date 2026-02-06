"""Space inspector skill for analyzing and exporting configurations."""

import json
from typing import Optional
from datetime import datetime

from genie_mcp_server.tools.space_tools import get_genie_space, list_genie_spaces, delete_genie_space
from genie_mcp_server.tools.conversation_tools import list_conversations
from genie_mcp_server.models.protobuf_format import protobuf_to_config
from genie_mcp_server.skills.utils.config_analyzer import ConfigAnalyzer


def run(
    space_id: str,
    mode: str = "health",
    compare_with: Optional[str] = None,
    search_tables: Optional[str] = None,
    search_keywords: Optional[str] = None,
    output_file: Optional[str] = None,
) -> str:
    """Inspect space configuration and health.

    Args:
        space_id: Space ID to inspect.
        mode: Operation mode (health, export, diff, find).
        compare_with: Second space ID for diff mode.
        search_tables: Comma-separated table names for find mode.
        search_keywords: Comma-separated keywords for find mode.
        output_file: Output file path for export mode.

    Returns:
        Formatted markdown result.
    """
    if mode == "health":
        return _health_check(space_id)
    elif mode == "export":
        return _export_config(space_id, output_file)
    elif mode == "diff":
        if not compare_with:
            return "❌ **Error:** diff mode requires compare_with parameter"
        return _diff_configs(space_id, compare_with)
    elif mode == "find":
        tables = [t.strip() for t in search_tables.split(",")] if search_tables else None
        keywords = [k.strip() for k in search_keywords.split(",")] if search_keywords else None
        return _find_spaces(tables, keywords)
    else:
        return f"❌ **Error:** Unknown mode '{mode}'. Use: health, export, diff, or find"


def _health_check(space_id: str) -> str:
    """Perform health check on a space.

    Args:
        space_id: Space ID.

    Returns:
        Formatted health report.
    """
    try:
        # Get space with config
        space_json = get_genie_space(space_id, include_serialized_space=True)
        space = json.loads(space_json)
        space_name = space.get("title", "Unknown")

        # Parse config
        serialized_space = space.get("serialized_space")
        if not serialized_space:
            return f"❌ **Error:** No configuration found for space '{space_name}'"

        config_obj = protobuf_to_config(serialized_space)
        config = config_obj.model_dump()

        # Get conversation history
        try:
            conversations_json = list_conversations(space_id)
            conversations = json.loads(conversations_json).get("conversations", [])
            conversation_count = len(conversations)

            # Find most recent conversation
            last_activity = None
            if conversations:
                # Assuming conversations have created_timestamp
                timestamps = [
                    datetime.fromisoformat(c.get("created_timestamp", "").replace("Z", "+00:00"))
                    for c in conversations
                    if c.get("created_timestamp")
                ]
                if timestamps:
                    last_activity = max(timestamps)

        except Exception:
            conversation_count = 0
            last_activity = None

        # Generate health report
        analyzer = ConfigAnalyzer()
        return analyzer.generate_health_report(
            space_name=space_name,
            config=config,
            conversation_count=conversation_count,
            last_activity=last_activity
        )

    except Exception as e:
        return f"❌ **Error:** {str(e)}"


def _export_config(space_id: str, output_file: Optional[str] = None) -> str:
    """Export space configuration as JSON.

    Args:
        space_id: Space ID.
        output_file: Optional output file path.

    Returns:
        Formatted export result.
    """
    try:
        # Get space with config
        space_json = get_genie_space(space_id, include_serialized_space=True)
        space = json.loads(space_json)
        space_name = space.get("title", "Unknown")

        # Parse config
        serialized_space = space.get("serialized_space")
        if not serialized_space:
            return f"❌ **Error:** No configuration found for space '{space_name}'"

        config_obj = protobuf_to_config(serialized_space)
        config = config_obj.model_dump()

        # Format output
        output = f"# 📦 Configuration Export: {space_name}\n\n"
        output += f"**Space ID:** `{space_id}`\n\n"

        # Summary
        output += "## Summary\n\n"
        output += f"- **Tables:** {len(config.get('tables', []))}\n"
        output += f"- **Instructions:** {len(config.get('instructions', []))}\n"
        output += f"- **Example Queries:** {len(config.get('example_sql_queries', []))}\n"

        snippets = config.get("sql_snippets", {})
        if snippets:
            output += f"- **SQL Measures:** {len(snippets.get('measures', []))}\n"
            output += f"- **SQL Expressions:** {len(snippets.get('expressions', []))}\n"
            output += f"- **SQL Filters:** {len(snippets.get('filters', []))}\n"

        joins = config.get("join_specifications", [])
        if joins:
            output += f"- **Join Specifications:** {len(joins)}\n"

        output += "\n"

        # Configuration JSON
        output += "## Configuration JSON\n\n"
        output += "```json\n"
        output += json.dumps(config, indent=2)
        output += "\n```\n\n"

        # Save to file if requested
        if output_file:
            try:
                with open(output_file, "w") as f:
                    json.dump(config, f, indent=2)
                output += f"✅ **Saved to:** `{output_file}`\n"
            except Exception as e:
                output += f"⚠️ **File save error:** {str(e)}\n"

        return output

    except Exception as e:
        return f"❌ **Error:** {str(e)}"


def _diff_configs(space_id_1: str, space_id_2: str) -> str:
    """Compare configurations of two spaces.

    Args:
        space_id_1: First space ID.
        space_id_2: Second space ID.

    Returns:
        Formatted diff result.
    """
    try:
        client = GenieClient()

        # Get both spaces
        space1 = client.get_space(space_id_1, include_serialized_space=True)
        space2 = client.get_space(space_id_2, include_serialized_space=True)

        name1 = space1.get("name", "Space 1")
        name2 = space2.get("name", "Space 2")

        # Parse configs
        config1 = protobuf_to_config(space1["serialized_space"]).model_dump()
        config2 = protobuf_to_config(space2["serialized_space"]).model_dump()

        # Build diff report
        output = f"# 🔍 Configuration Diff\n\n"
        output += f"**Space 1:** {name1} (`{space_id_1}`)\n"
        output += f"**Space 2:** {name2} (`{space_id_2}`)\n\n"

        # Compare metrics
        output += "## Comparison\n\n"
        output += "| Metric | Space 1 | Space 2 | Difference |\n"
        output += "|--------|---------|---------|------------|\n"

        # Tables
        tables1 = len(config1.get("tables", []))
        tables2 = len(config2.get("tables", []))
        output += f"| Tables | {tables1} | {tables2} | {tables2 - tables1:+d} |\n"

        # Instructions
        instr1 = len(config1.get("instructions", []))
        instr2 = len(config2.get("instructions", []))
        output += f"| Instructions | {instr1} | {instr2} | {instr2 - instr1:+d} |\n"

        # Examples
        ex1 = len(config1.get("example_sql_queries", []))
        ex2 = len(config2.get("example_sql_queries", []))
        output += f"| Example Queries | {ex1} | {ex2} | {ex2 - ex1:+d} |\n"

        # Snippets
        snippets1 = config1.get("sql_snippets", {})
        snippets2 = config2.get("sql_snippets", {})
        meas1 = len(snippets1.get("measures", []))
        meas2 = len(snippets2.get("measures", []))
        output += f"| SQL Measures | {meas1} | {meas2} | {meas2 - meas1:+d} |\n"

        expr1 = len(snippets1.get("expressions", []))
        expr2 = len(snippets2.get("expressions", []))
        output += f"| SQL Expressions | {expr1} | {expr2} | {expr2 - expr1:+d} |\n"

        # Joins
        joins1 = len(config1.get("join_specifications", []))
        joins2 = len(config2.get("join_specifications", []))
        output += f"| Join Specifications | {joins1} | {joins2} | {joins2 - joins1:+d} |\n"

        output += "\n"

        # Table differences
        table_ids1 = set(
            f"{t['catalog_name']}.{t['schema_name']}.{t['table_name']}"
            for t in config1.get("tables", [])
        )
        table_ids2 = set(
            f"{t['catalog_name']}.{t['schema_name']}.{t['table_name']}"
            for t in config2.get("tables", [])
        )

        only_in_1 = table_ids1 - table_ids2
        only_in_2 = table_ids2 - table_ids1

        if only_in_1 or only_in_2:
            output += "## Table Differences\n\n"
            if only_in_1:
                output += "**Only in Space 1:**\n"
                for table in sorted(only_in_1):
                    output += f"- {table}\n"
                output += "\n"
            if only_in_2:
                output += "**Only in Space 2:**\n"
                for table in sorted(only_in_2):
                    output += f"- {table}\n"
                output += "\n"

        return output

    except Exception as e:
        return f"❌ **Error:** {str(e)}"


def _find_spaces(
    search_tables: Optional[list[str]] = None,
    search_keywords: Optional[list[str]] = None
) -> str:
    """Find spaces by table or keyword.

    Args:
        search_tables: Table names to search for.
        search_keywords: Keywords to search for.

    Returns:
        Formatted search results.
    """
    if not search_tables and not search_keywords:
        return "❌ **Error:** Provide at least one of search_tables or search_keywords"

    try:
        all_spaces_json = list_genie_spaces()
        all_spaces = json.loads(all_spaces_json).get("spaces", [])

        matching_spaces = []

        for space in all_spaces:
            space_id = space["space_id"]
            space_name = space["title"]

            # Get config
            try:
                space_detail_json = get_genie_space(space_id, include_serialized_space=True)
                space_detail = json.loads(space_detail_json)
                serialized_space = space_detail.get("serialized_space")
                if not serialized_space:
                    continue

                config = protobuf_to_config(serialized_space).model_dump()

                # Check tables
                if search_tables:
                    space_tables = [
                        f"{t['catalog_name']}.{t['schema_name']}.{t['table_name']}"
                        for t in config.get("tables", [])
                    ]

                    for search_table in search_tables:
                        if any(search_table.lower() in st.lower() for st in space_tables):
                            matching_spaces.append({
                                "space_id": space_id,
                                "name": space_name,
                                "match_reason": f"Contains table matching '{search_table}'"
                            })
                            break

                # Check keywords
                if search_keywords:
                    searchable_text = " ".join([
                        space_name,
                        config.get("description", ""),
                        " ".join(i.get("content", "") for i in config.get("instructions", []))
                    ]).lower()

                    for keyword in search_keywords:
                        if keyword.lower() in searchable_text:
                            matching_spaces.append({
                                "space_id": space_id,
                                "name": space_name,
                                "match_reason": f"Contains keyword '{keyword}'"
                            })
                            break

            except Exception:
                continue  # Skip spaces with errors

        # Format results
        output = "# 🔍 Space Search Results\n\n"
        output += f"**Search criteria:**\n"
        if search_tables:
            output += f"- Tables: {', '.join(search_tables)}\n"
        if search_keywords:
            output += f"- Keywords: {', '.join(search_keywords)}\n"
        output += "\n"

        if not matching_spaces:
            output += "_No matching spaces found_\n"
        else:
            output += f"**Found {len(matching_spaces)} matching space(s):**\n\n"
            for space in matching_spaces:
                output += f"### {space['name']}\n"
                output += f"- **Space ID:** `{space['space_id']}`\n"
                output += f"- **Match:** {space['match_reason']}\n\n"

        return output

    except Exception as e:
        return f"❌ **Error:** {str(e)}"
