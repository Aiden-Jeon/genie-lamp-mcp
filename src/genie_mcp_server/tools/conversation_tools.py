"""Genie conversation and query tools for MCP server."""

import asyncio
import json
from typing import Any, Optional

from databricks.sdk import WorkspaceClient

from genie_mcp_server.client.polling import poll_until_complete
from genie_mcp_server.utils.error_handling import translate_databricks_error
from genie_mcp_server.utils.rate_limiter import genie_rate_limiter

# Global client instance - will be set by server.py
_workspace_client: Optional[WorkspaceClient] = None


def set_workspace_client(client: WorkspaceClient) -> None:
    """Set the global workspace client instance.

    Args:
        client: WorkspaceClient instance to use for all tool operations
    """
    global _workspace_client
    _workspace_client = client


def get_workspace_client() -> WorkspaceClient:
    """Get the global workspace client instance.

    Returns:
        WorkspaceClient instance

    Raises:
        RuntimeError: If client not initialized
    """
    if _workspace_client is None:
        raise RuntimeError("Workspace client not initialized. Call set_workspace_client first.")
    return _workspace_client


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
    client = get_workspace_client()

    try:
        # Apply rate limiting
        await genie_rate_limiter.acquire()

        # Start conversation
        conversation = client.genie.start_conversation(space_id=space_id, content=question)

        conversation_id = conversation.conversation_id
        message_id = conversation.message_id

        # Poll for completion
        def check_status() -> tuple[bool, dict[str, Any]]:
            message = client.genie.get_message(space_id=space_id, conversation_id=conversation_id, message_id=message_id)

            status = message.status.value if hasattr(message.status, "value") else str(message.status)

            # Check if completed or failed
            if status in ["COMPLETED", "FAILED", "CANCELLED"]:
                result = {
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "status": status,
                    "response_text": getattr(message, "content", None),
                    "error": getattr(message, "error", None),
                }

                # Try to fetch SQL query and results
                if status == "COMPLETED":
                    try:
                        # Get attachments (query results)
                        if hasattr(message, "attachments") and message.attachments:
                            for attachment in message.attachments:
                                if hasattr(attachment, "query"):
                                    query_info = attachment.query
                                    result["sql_query"] = getattr(query_info, "query", None)

                                    # Fetch query results
                                    if hasattr(query_info, "query_result_id"):
                                        query_result = client.genie.get_message_query_result(
                                            space_id=space_id,
                                            conversation_id=conversation_id,
                                            message_id=message_id,
                                        )
                                        result["query_result"] = _format_query_result(query_result)
                    except Exception:
                        # Don't fail if we can't fetch results
                        pass

                return True, result

            return False, {}

        result = await poll_until_complete(
            check_fn=check_status,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        raise translate_databricks_error(e)


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
    client = get_workspace_client()

    try:
        # Apply rate limiting
        await genie_rate_limiter.acquire()

        # Send follow-up message
        message = client.genie.create_message(
            space_id=space_id, conversation_id=conversation_id, content=question
        )

        message_id = message.message_id

        # Poll for completion (same logic as ask_genie)
        def check_status() -> tuple[bool, dict[str, Any]]:
            msg = client.genie.get_message(
                space_id=space_id, conversation_id=conversation_id, message_id=message_id
            )

            status = msg.status.value if hasattr(msg.status, "value") else str(msg.status)

            if status in ["COMPLETED", "FAILED", "CANCELLED"]:
                result = {
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "status": status,
                    "response_text": getattr(msg, "content", None),
                    "error": getattr(msg, "error", None),
                }

                if status == "COMPLETED":
                    try:
                        if hasattr(msg, "attachments") and msg.attachments:
                            for attachment in msg.attachments:
                                if hasattr(attachment, "query"):
                                    query_info = attachment.query
                                    result["sql_query"] = getattr(query_info, "query", None)

                                    if hasattr(query_info, "query_result_id"):
                                        query_result = client.genie.get_message_query_result(
                                            space_id=space_id,
                                            conversation_id=conversation_id,
                                            message_id=message_id,
                                        )
                                        result["query_result"] = _format_query_result(query_result)
                    except Exception:
                        pass

                return True, result

            return False, {}

        result = await poll_until_complete(
            check_fn=check_status,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        raise translate_databricks_error(e)


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
    client = get_workspace_client()

    try:
        query_result = client.genie.get_message_query_result(
            space_id=space_id, conversation_id=conversation_id, message_id=message_id
        )

        result = _format_query_result(query_result)
        return json.dumps(result, indent=2)

    except Exception as e:
        raise translate_databricks_error(e)


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
    client = get_workspace_client()

    try:
        result = client.genie.list_conversations(
            space_id=space_id, page_size=page_size, page_token=page_token
        )

        conversations = []
        for conv in result.conversations or []:
            conversations.append(
                {
                    "conversation_id": conv.conversation_id,
                    "space_id": space_id,
                    "title": getattr(conv, "title", None),
                    "created_timestamp": getattr(conv, "created_timestamp", None),
                    "updated_timestamp": getattr(conv, "updated_timestamp", None),
                }
            )

        return json.dumps(
            {"conversations": conversations, "next_page_token": result.next_page_token}, indent=2
        )

    except Exception as e:
        raise translate_databricks_error(e)


def get_conversation_history(space_id: str, conversation_id: str) -> str:
    """Get all messages in a conversation.

    Args:
        space_id: Unique identifier for the Genie space
        conversation_id: ID of the conversation

    Returns:
        JSON string with complete conversation thread
    """
    client = get_workspace_client()

    try:
        result = client.genie.get_conversation(space_id=space_id, conversation_id=conversation_id)

        messages = []
        if hasattr(result, "messages"):
            for msg in result.messages or []:
                messages.append(
                    {
                        "message_id": msg.message_id,
                        "content": getattr(msg, "content", None),
                        "status": msg.status.value
                        if hasattr(msg.status, "value")
                        else str(msg.status),
                        "created_timestamp": getattr(msg, "created_timestamp", None),
                    }
                )

        return json.dumps(
            {
                "conversation_id": conversation_id,
                "space_id": space_id,
                "title": getattr(result, "title", None),
                "messages": messages,
            },
            indent=2,
        )

    except Exception as e:
        raise translate_databricks_error(e)


def _format_query_result(query_result: Any) -> dict[str, Any]:
    """Format query result object into a dictionary.

    Args:
        query_result: Query result object from Databricks SDK

    Returns:
        Dictionary with formatted results
    """
    result = {"rows": [], "schema": []}

    # Extract schema
    if hasattr(query_result, "statement_response"):
        stmt_resp = query_result.statement_response
        if hasattr(stmt_resp, "manifest") and hasattr(stmt_resp.manifest, "schema"):
            schema = stmt_resp.manifest.schema
            if hasattr(schema, "columns"):
                result["schema"] = [
                    {"name": col.name, "type": getattr(col, "type_text", None)}
                    for col in schema.columns or []
                ]

        # Extract rows
        if hasattr(stmt_resp, "result") and hasattr(stmt_resp.result, "data_array"):
            result["rows"] = stmt_resp.result.data_array or []
            result["row_count"] = len(result["rows"])

    return result
