"""Bulk operations skill for batch updates and management."""

import asyncio
import json
import re
from typing import Optional

from genie_mcp_server.tools.space_tools import get_genie_space, list_genie_spaces, delete_genie_space
from genie_mcp_server.models.protobuf_format import protobuf_to_config


def run(
    operation: str,
    space_ids: Optional[str] = None,
    pattern: Optional[str] = None,
    add_instructions: Optional[str] = None,
    add_tables: Optional[str] = None,
    dry_run: bool = True,
) -> str:
    """Bulk operations on multiple spaces.

    Args:
        operation: Operation type (update, delete, clone).
        space_ids: Comma-separated space IDs for update/clone.
        pattern: Pattern for delete (glob or regex).
        add_instructions: Instructions to add (newline-separated).
        add_tables: Tables to add (comma-separated: catalog.schema.table).
        dry_run: Preview changes without executing (default: True).

    Returns:
        Formatted markdown result.
    """
    if operation == "update":
        if not space_ids:
            return "❌ **Error:** update operation requires space_ids"
        ids = [s.strip() for s in space_ids.split(",") if s.strip()]
        instructions = [i.strip() for i in add_instructions.split("\n") if i.strip()] if add_instructions else None
        tables = [t.strip() for t in add_tables.split(",") if t.strip()] if add_tables else None
        return _bulk_update(ids, instructions, tables, dry_run)

    elif operation == "delete":
        if not pattern and not space_ids:
            return "❌ **Error:** delete operation requires pattern or space_ids"
        if space_ids:
            ids = [s.strip() for s in space_ids.split(",") if s.strip()]
            return _bulk_delete_by_ids(ids, dry_run)
        else:
            return _bulk_delete_by_pattern(pattern, dry_run)

    elif operation == "clone":
        if not space_ids or "," in space_ids:
            return "❌ **Error:** clone operation requires exactly one space_id"
        return "❌ **Error:** Clone operation not yet implemented"

    else:
        return f"❌ **Error:** Unknown operation '{operation}'. Use: update, delete, or clone"


def _bulk_update(
    space_ids: list[str],
    add_instructions: Optional[list[str]] = None,
    add_tables: Optional[list[str]] = None,
    dry_run: bool = True
) -> str:
    """Bulk update multiple spaces.

    Args:
        space_ids: List of space IDs.
        add_instructions: Instructions to add.
        add_tables: Tables to add (format: catalog.schema.table).
        dry_run: Preview only.

    Returns:
        Formatted result.
    """
    if not add_instructions and not add_tables:
        return "❌ **Error:** Specify at least one of add_instructions or add_tables"

    output = f"# 🔄 Bulk Update: {len(space_ids)} Space(s)\n\n"

    if dry_run:
        output += "⚠️ **DRY RUN MODE** - No changes will be made\n\n"

    output += "## Changes to Apply\n\n"
    if add_instructions:
        output += f"**Add Instructions:** {len(add_instructions)}\n"
        for i, instr in enumerate(add_instructions, 1):
            output += f"  {i}. {instr}\n"
        output += "\n"
    if add_tables:
        output += f"**Add Tables:** {len(add_tables)}\n"
        for table in add_tables:
            output += f"  - {table}\n"
        output += "\n"

    # Process each space
    results = []

    for space_id in space_ids:
        try:
            # Get space config
            space_json = get_genie_space(space_id, include_serialized_space=True)
            space = json.loads(space_json)
            space_name = space.get("title", "Unknown")

            if not space.get("serialized_space"):
                results.append({
                    "space_id": space_id,
                    "name": space_name,
                    "success": False,
                    "error": "No configuration found"
                })
                continue

            # Parse config
            config_obj = protobuf_to_config(space["serialized_space"])
            config = config_obj.model_dump()

            # Apply changes
            modified = False

            if add_instructions:
                existing_instructions = config.get("instructions", [])
                for instr in add_instructions:
                    existing_instructions.append({"content": instr})
                config["instructions"] = existing_instructions
                modified = True

            if add_tables:
                existing_tables = config.get("tables", [])
                for table_str in add_tables:
                    parts = table_str.split(".")
                    if len(parts) == 3:
                        existing_tables.append({
                            "catalog_name": parts[0],
                            "schema_name": parts[1],
                            "table_name": parts[2]
                        })
                        modified = True
                config["tables"] = existing_tables

            # Update space (if not dry run)
            if not dry_run and modified:
                # Note: update_genie_space expects warehouse_id and config
                # This is a limitation - we'd need to get the warehouse_id from somewhere
                results.append({
                    "space_id": space_id,
                    "name": space_name,
                    "success": False,
                    "error": "Update not implemented (requires warehouse_id)"
                })
            else:
                results.append({
                    "space_id": space_id,
                    "name": space_name,
                    "success": True,
                    "error": None
                })

        except Exception as e:
            results.append({
                "space_id": space_id,
                "name": "Unknown",
                "success": False,
                "error": str(e)
            })

    # Format results
    output += "## Results\n\n"
    success_count = sum(1 for r in results if r["success"])
    failure_count = len(results) - success_count

    for result in results:
        icon = "✅" if result["success"] else "❌"
        output += f"{icon} **{result['name']}** (`{result['space_id']}`)\n"
        if result["error"]:
            output += f"   - Error: {result['error']}\n"
        output += "\n"

    output += "## Summary\n\n"
    output += f"- **Successful:** {success_count} space(s)\n"
    output += f"- **Failed:** {failure_count} space(s)\n"

    if dry_run:
        output += "\n⚠️ **To apply changes, set dry_run=False**\n"

    return output


def _bulk_delete_by_ids(space_ids: list[str], dry_run: bool = True) -> str:
    """Delete multiple spaces by ID.

    Args:
        space_ids: List of space IDs.
        dry_run: Preview only.

    Returns:
        Formatted result.
    """
    output = f"# 🗑️ Bulk Delete: {len(space_ids)} Space(s)\n\n"

    if dry_run:
        output += "⚠️ **DRY RUN MODE** - No deletions will be performed\n\n"
    else:
        output += "⚠️ **DESTRUCTIVE OPERATION** - Spaces will be permanently deleted\n\n"

    results = []

    for space_id in space_ids:
        try:
            # Get space info
            space_json = get_genie_space(space_id)
            space = json.loads(space_json)
            space_name = space.get("title", "Unknown")

            # Delete if not dry run
            if not dry_run:
                delete_genie_space(space_id)

            results.append({
                "space_id": space_id,
                "name": space_name,
                "success": True,
                "error": None
            })

        except Exception as e:
            results.append({
                "space_id": space_id,
                "name": "Unknown",
                "success": False,
                "error": str(e)
            })

    # Format results
    output += "## Results\n\n"
    success_count = sum(1 for r in results if r["success"])
    failure_count = len(results) - success_count

    for result in results:
        icon = "✅" if result["success"] else "❌"
        action = "Deleted" if not dry_run else "Would delete"
        output += f"{icon} **{action}:** {result['name']} (`{result['space_id']}`)\n"
        if result["error"]:
            output += f"   - Error: {result['error']}\n"
        output += "\n"

    output += "## Summary\n\n"
    output += f"- **Successful:** {success_count} space(s)\n"
    output += f"- **Failed:** {failure_count} space(s)\n"

    if dry_run:
        output += "\n⚠️ **To permanently delete, set dry_run=False**\n"

    return output


def _bulk_delete_by_pattern(pattern: str, dry_run: bool = True) -> str:
    """Delete spaces matching a pattern.

    Args:
        pattern: Glob or regex pattern.
        dry_run: Preview only.

    Returns:
        Formatted result.
    """
    try:
        all_spaces_json = list_genie_spaces()
        all_spaces = json.loads(all_spaces_json).get("spaces", [])

        # Convert glob pattern to regex if needed
        if "*" in pattern or "?" in pattern:
            # Simple glob to regex conversion
            regex_pattern = pattern.replace(".", r"\.")
            regex_pattern = regex_pattern.replace("*", ".*")
            regex_pattern = regex_pattern.replace("?", ".")
            regex_pattern = f"^{regex_pattern}$"
        else:
            regex_pattern = pattern

        # Find matching spaces
        matching_spaces = []
        for space in all_spaces:
            if re.match(regex_pattern, space["title"], re.IGNORECASE):
                matching_spaces.append(space)

        if not matching_spaces:
            return f"# 🗑️ Bulk Delete\n\n_No spaces matching pattern '{pattern}'_\n"

        # Use the ID-based delete function
        space_ids = [s["space_id"] for s in matching_spaces]
        return _bulk_delete_by_ids(space_ids, dry_run)

    except re.error as e:
        return f"❌ **Error:** Invalid pattern: {str(e)}"
    except Exception as e:
        return f"❌ **Error:** {str(e)}"
