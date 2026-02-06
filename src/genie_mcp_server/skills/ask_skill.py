"""Q&A assistant skill for conversational Genie queries."""

import asyncio
import json
from typing import Optional

from genie_mcp_server.skills import conversation_manager
from genie_mcp_server.skills.utils.result_formatter import ResultFormatter
from genie_mcp_server.tools.conversation_tools import ask_genie as ask_genie_tool, continue_conversation as continue_conversation_tool
from genie_mcp_server.tools.space_tools import list_genie_spaces


def run(
    question: str,
    space_id: Optional[str] = None,
    space_name: Optional[str] = None,
    new_conversation: bool = False,
    preview_only: bool = False,
    timeout: int = 300,
    verbose: bool = False,
) -> str:
    """Ask questions to Genie spaces with smart conversation tracking.

    Args:
        question: The question to ask.
        space_id: Explicit space ID (takes precedence).
        space_name: Search for space by name (case-insensitive).
        new_conversation: Force new conversation (don't continue).
        preview_only: Show SQL without executing (not implemented yet).
        timeout: Query timeout in seconds (default: 300).
        verbose: Show detailed results (all rows).

    Returns:
        Formatted markdown result.
    """
    formatter = ResultFormatter()

    # Step 1: Space selection
    selected_space_id = _select_space(space_id, space_name)
    if not selected_space_id:
        return formatter.format_error(
            "No space ID provided and no recent conversation found. "
            "Please provide space_id or space_name.",
            question
        )

    # Step 2: Conversation tracking
    conversation_id, is_new = conversation_manager.get_or_create(
        space_id=selected_space_id,
        force_new=new_conversation
    )

    # Step 3: Execute query
    try:
        if is_new or not conversation_id:
            # Start new conversation
            result = asyncio.run(_ask_genie(
                space_id=selected_space_id,
                question=question,
                timeout=timeout
            ))
        else:
            # Continue existing conversation
            result = asyncio.run(_continue_conversation(
                space_id=selected_space_id,
                conversation_id=conversation_id,
                question=question,
                timeout=timeout
            ))

        # Update conversation state
        conversation_manager.update(
            space_id=selected_space_id,
            conversation_id=result["conversation_id"],
            message_id=result.get("message_id", "")
        )

        # Format result
        return formatter.format(result, question, verbose)

    except asyncio.TimeoutError:
        return formatter.format_timeout(question, timeout)
    except Exception as e:
        error_msg = str(e)

        # Check for rate limiting
        if "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
            return formatter.format_rate_limit(question, wait_seconds=60)

        return formatter.format_error(error_msg, question)


def _select_space(
    space_id: Optional[str],
    space_name: Optional[str]
) -> Optional[str]:
    """Select the space to query.

    Args:
        space_id: Explicit space ID.
        space_name: Space name to search for.

    Returns:
        Selected space ID or None.
    """
    # Explicit ID takes precedence
    if space_id:
        return space_id

    # Search by name
    if space_name:
        try:
            spaces_json = list_genie_spaces()
            spaces_data = json.loads(spaces_json)
            spaces = spaces_data.get("spaces", [])

            # Case-insensitive search
            for space in spaces:
                if space["title"].lower() == space_name.lower():
                    return space["space_id"]

            # Partial match fallback
            for space in spaces:
                if space_name.lower() in space["title"].lower():
                    return space["space_id"]

        except Exception:
            pass  # Fall through to last space

    # Fallback to last used space
    return conversation_manager.get_last_space()


async def _ask_genie(
    space_id: str,
    question: str,
    timeout: int
) -> dict:
    """Start a new conversation with Genie.

    Args:
        space_id: Space ID.
        question: Question to ask.
        timeout: Timeout in seconds.

    Returns:
        Query result dict.
    """
    # Use existing ask_genie tool
    result_json = await ask_genie_tool(
        space_id=space_id,
        question=question,
        timeout_seconds=timeout
    )
    return json.loads(result_json)


async def _continue_conversation(
    space_id: str,
    conversation_id: str,
    question: str,
    timeout: int
) -> dict:
    """Continue an existing conversation.

    Args:
        space_id: Space ID.
        conversation_id: Existing conversation ID.
        question: Follow-up question.
        timeout: Timeout in seconds.

    Returns:
        Query result dict.
    """
    # Use existing continue_conversation tool
    result_json = await continue_conversation_tool(
        space_id=space_id,
        conversation_id=conversation_id,
        content=question,
        timeout_seconds=timeout
    )
    return json.loads(result_json)
