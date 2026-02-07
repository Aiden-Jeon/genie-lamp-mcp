"""Space creation wizard skill for guided Genie space setup."""

import json
from typing import Optional

from genie_mcp_server.tools.space_tools import create_genie_space
from genie_mcp_server.tools.conversation_tools import get_workspace_client
from genie_mcp_server.skills.utils.warehouse_discovery import WarehouseDiscovery
from genie_mcp_server.skills.utils.space_orchestrator import SpaceOrchestrator


def run(
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

    Args:
        catalog_name: Unity Catalog name (e.g., "main").
        schema_name: Schema name (e.g., "sales").
        table_names: Comma-separated table names (e.g., "orders,customers").
        warehouse_id: SQL warehouse ID (auto-discovered if None).
        domain: Domain template (minimal, sales, customer, inventory, financial, hr).
        space_name: Optional custom space name.
        quick: Quick mode - create immediately with minimal validation.
        expert: Expert mode - return config for manual editing.

    Returns:
        Formatted markdown result.
    """
    try:
        # Parse table names
        tables = [t.strip() for t in table_names.split(",") if t.strip()]
        if not tables:
            return "❌ **Error:** No tables specified. Provide at least one table name."

        # Step 1: Warehouse discovery
        client = get_workspace_client()
        discovery = WarehouseDiscovery(client)

        if not warehouse_id:
            warehouse_id = discovery.get_recommended_warehouse("development")
            if not warehouse_id:
                return (
                    "❌ **Error:** No SQL warehouses available.\n\n"
                    "Please create a warehouse first or specify warehouse_id manually."
                )
            warehouse_info = discovery.get_warehouse_info(warehouse_id)
            warehouse_note = f" (auto-discovered: {warehouse_info['name']})" if warehouse_info else ""
        else:
            warehouse_info = discovery.get_warehouse_info(warehouse_id)
            if not warehouse_info:
                return f"❌ **Error:** Warehouse ID '{warehouse_id}' not found."
            warehouse_note = f" ({warehouse_info['name']})"

        # Step 2: Generate config from template
        orchestrator = SpaceOrchestrator()

        try:
            config = orchestrator.generate_config_from_template(
                domain=domain,
                catalog_name=catalog_name,
                schema_name=schema_name,
                table_names=tables,
                space_name=space_name,
            )
        except Exception as e:
            return f"❌ **Error generating config:** {str(e)}"

        # Step 3: Validate config
        validation = orchestrator.validate_and_score(config, validate_sql=False)

        # Step 4: Decide on mode
        if expert:
            # Expert mode: return config for editing
            return _format_expert_mode(config, validation, warehouse_id, warehouse_note)

        if quick or validation["score"] >= 80:
            # Quick mode or high score: create immediately
            return _create_space(
                warehouse_id=warehouse_id,
                config=config,
                validation=validation,
                warehouse_note=warehouse_note,
                quick=quick
            )

        # Guided mode: show validation feedback
        return _format_guided_mode(config, validation, warehouse_id, warehouse_note)

    except Exception as e:
        return f"❌ **Error:** {str(e)}"


def _create_space(
    warehouse_id: str,
    config: dict,
    validation: dict,
    warehouse_note: str,
    quick: bool = False
) -> str:
    """Create the Genie space.

    Args:
        warehouse_id: SQL warehouse ID.
        config: GenieSpaceConfig dict.
        validation: Validation result.
        warehouse_note: Warehouse info note.
        quick: Whether this is quick mode.

    Returns:
        Formatted success/error message.
    """
    try:
        # Use create_genie_space tool
        space_json = create_genie_space(
            warehouse_id=warehouse_id,
            config_json=json.dumps(config)
        )
        space = json.loads(space_json)

        # Format success message
        output = "# ✅ Space Created Successfully\n\n"
        output += f"**Space ID:** `{space['space_id']}`\n"
        output += f"**Space Name:** {config['space_name']}\n"
        output += f"**Warehouse:** `{warehouse_id}`{warehouse_note}\n"
        output += f"**Validation Score:** {validation['score']}/100\n\n"

        # Configuration summary
        output += "## Configuration\n\n"
        output += f"- **Domain:** {config.get('domain', 'custom')}\n"
        output += f"- **Tables:** {len(config['tables'])}\n"
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

        # Warnings and recommendations
        if validation.get("warnings"):
            output += "## Warnings\n\n"
            for warning in validation["warnings"]:
                output += f"⚠️ {warning}\n"
            output += "\n"

        if validation.get("recommendations"):
            output += "## Recommendations\n\n"
            for rec in validation["recommendations"]:
                output += f"- {rec}\n"
            output += "\n"

        # Next steps
        output += "## Next Steps\n\n"
        output += f"1. **Ask questions:** Use `/ask` with space_id=`{space['space_id']}`\n"
        output += f"2. **View in UI:** Open Genie Spaces in your Databricks workspace\n"
        output += f"3. **Inspect health:** Use `/inspect` with space_id=`{space['space_id']}`\n"
        output += f"4. **Update config:** Use `/bulk` to add more instructions or snippets\n"

        return output

    except Exception as e:
        return f"❌ **Error creating space:** {str(e)}"


def _format_expert_mode(
    config: dict,
    validation: dict,
    warehouse_id: str,
    warehouse_note: str
) -> str:
    """Format expert mode output (return config for editing).

    Args:
        config: GenieSpaceConfig dict.
        validation: Validation result.
        warehouse_id: Warehouse ID.
        warehouse_note: Warehouse info note.

    Returns:
        Formatted markdown with config JSON.
    """
    output = "# 🔧 Expert Mode: Review Configuration\n\n"
    output += f"**Warehouse:** `{warehouse_id}`{warehouse_note}\n"
    output += f"**Validation Score:** {validation['score']}/100\n\n"

    if not validation["valid"]:
        output += "⚠️ **Validation Errors:**\n\n"
        for error in validation.get("errors", []):
            output += f"- {error}\n"
        output += "\n"

    if validation.get("recommendations"):
        output += "**Recommendations:**\n\n"
        for rec in validation["recommendations"]:
            output += f"- {rec}\n"
        output += "\n"

    output += "## Configuration JSON\n\n"
    output += "Review and edit the configuration below, then use the `create_genie_space` tool directly:\n\n"
    output += "```json\n"
    output += json.dumps(config, indent=2)
    output += "\n```\n\n"

    output += "## Create Space\n\n"
    output += "To create the space with this configuration:\n\n"
    output += "```python\n"
    output += f"create_genie_space(\n"
    output += f"    warehouse_id='{warehouse_id}',\n"
    output += f"    config_json=<your_modified_config>\n"
    output += f")\n"
    output += "```\n"

    return output


def _format_guided_mode(
    config: dict,
    validation: dict,
    warehouse_id: str,
    warehouse_note: str
) -> str:
    """Format guided mode output (validation feedback).

    Args:
        config: GenieSpaceConfig dict.
        validation: Validation result.
        warehouse_id: Warehouse ID.
        warehouse_note: Warehouse info note.

    Returns:
        Formatted markdown with validation feedback.
    """
    output = "# 🔍 Guided Mode: Configuration Review\n\n"
    output += f"**Warehouse:** `{warehouse_id}`{warehouse_note}\n"
    output += f"**Validation Score:** {validation['score']}/100\n\n"

    # Score interpretation
    if validation["score"] >= 90:
        output += "✅ **Excellent** - Configuration is ready to use\n\n"
    elif validation["score"] >= 70:
        output += "✅ **Good** - Configuration is functional\n\n"
    elif validation["score"] >= 50:
        output += "⚠️ **Fair** - Configuration needs improvement\n\n"
    else:
        output += "❌ **Poor** - Configuration has significant issues\n\n"

    # Validation errors
    if not validation["valid"]:
        output += "## Validation Errors\n\n"
        for error in validation.get("errors", []):
            output += f"❌ {error}\n"
        output += "\n"

    # Warnings
    if validation.get("warnings"):
        output += "## Warnings\n\n"
        for warning in validation["warnings"]:
            output += f"⚠️ {warning}\n"
        output += "\n"

    # Recommendations
    if validation.get("recommendations"):
        output += "## Recommendations\n\n"
        for rec in validation["recommendations"]:
            output += f"- {rec}\n"
        output += "\n"

    # Configuration summary
    output += "## Configuration Summary\n\n"
    output += f"- **Space Name:** {config['space_name']}\n"
    output += f"- **Domain:** {config.get('domain', 'custom')}\n"
    output += f"- **Tables:** {len(config['tables'])}\n"
    output += f"- **Instructions:** {len(config.get('instructions', []))}\n"
    output += f"- **Example Queries:** {len(config.get('example_sql_queries', []))}\n\n"

    # Next steps
    output += "## Next Steps\n\n"
    output += "**Option 1: Create with current config**\n"
    output += "- Use `quick=True` to create immediately\n\n"
    output += "**Option 2: Edit config manually**\n"
    output += "- Use `expert=True` to get the full config JSON\n"
    output += "- Edit and use `create_genie_space` tool directly\n\n"
    output += "**Option 3: Improve config**\n"
    output += "- Address the recommendations above\n"
    output += "- Try a different domain template\n"

    return output
