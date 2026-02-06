"""Format Genie query results as markdown."""

from typing import Any, Optional


class ResultFormatter:
    """Format Genie query results as readable markdown."""

    def format(
        self,
        result: dict,
        question: str,
        verbose: bool = False
    ) -> str:
        """Adaptive formatting based on result shape.

        Args:
            result: Query result dict from ask_genie or continue_conversation.
            question: The original question asked.
            verbose: If True, show detailed results (all rows).

        Returns:
            Formatted markdown string.
        """
        # Extract components
        response_text = result.get("response_text", "No response")
        sql_query = result.get("sql_query")
        query_results = result.get("query_results")
        conversation_id = result.get("conversation_id", "")

        # Build markdown output
        output = f"### {question}\n\n"
        output += f"{response_text}\n\n"

        # Add results if present
        if query_results:
            output += self._format_results(query_results, verbose)
            output += "\n"

        # Add SQL (collapsible)
        if sql_query:
            output += "<details>\n<summary>📊 View SQL Query</summary>\n\n"
            output += f"```sql\n{sql_query}\n```\n</details>\n\n"

        # Add conversation ID
        output += f"**Conversation ID:** `{conversation_id}`\n\n"
        output += "💬 **Ask follow-up:** Use `/ask` with your next question\n"

        return output

    def _format_results(
        self,
        query_results: dict,
        verbose: bool = False
    ) -> str:
        """Format query results as markdown table.

        Args:
            query_results: Dict with 'columns' and 'rows' keys.
            verbose: If True, show all rows. Otherwise limit to 10.

        Returns:
            Markdown table string.
        """
        columns = query_results.get("columns", [])
        rows = query_results.get("rows", [])

        if not rows or not columns:
            return ""

        # Single value result
        if len(rows) == 1 and len(rows[0]) == 1:
            return f"**Answer:** {rows[0][0]}\n"

        # Table result
        max_rows = None if verbose else 10
        return self._format_table(columns, rows, max_rows)

    def _format_table(
        self,
        columns: list[str],
        rows: list[list[Any]],
        max_rows: Optional[int] = None
    ) -> str:
        """Format rows as markdown table.

        Args:
            columns: Column names.
            rows: Data rows.
            max_rows: Maximum rows to display (None for all).

        Returns:
            Markdown table string.
        """
        if not rows:
            return "_No results_\n"

        # Limit rows if needed
        display_rows = rows[:max_rows] if max_rows else rows
        truncated = len(rows) > len(display_rows)

        # Build table
        output = "| " + " | ".join(str(col) for col in columns) + " |\n"
        output += "| " + " | ".join("---" for _ in columns) + " |\n"

        for row in display_rows:
            formatted_row = [self._format_cell(cell) for cell in row]
            output += "| " + " | ".join(formatted_row) + " |\n"

        if truncated:
            output += f"\n_Showing {len(display_rows)} of {len(rows)} rows_\n"

        return output

    def _format_cell(self, value: Any) -> str:
        """Format a single cell value for display.

        Args:
            value: Cell value.

        Returns:
            Formatted string.
        """
        if value is None:
            return "_null_"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            # Escape pipes in strings
            return value.replace("|", "\\|")
        return str(value)

    def format_error(self, error: str, question: str) -> str:
        """Format an error message.

        Args:
            error: Error message.
            question: The original question.

        Returns:
            Formatted error markdown.
        """
        output = f"### {question}\n\n"
        output += f"⚠️ **Error:** {error}\n\n"
        output += "**Suggestions:**\n"
        output += "- Check that the space ID is correct\n"
        output += "- Verify you have access to the space\n"
        output += "- Try rephrasing your question\n"
        return output

    def format_timeout(self, question: str, timeout: int) -> str:
        """Format a timeout message.

        Args:
            question: The original question.
            timeout: Timeout duration in seconds.

        Returns:
            Formatted timeout markdown.
        """
        output = f"### {question}\n\n"
        output += f"⏳ **Query Timeout:** Query exceeded {timeout} seconds\n\n"
        output += "**Possible causes:**\n"
        output += "- Complex query on large dataset\n"
        output += "- Warehouse cold-starting\n"
        output += "- Network issues\n\n"
        output += "**Suggestions:**\n"
        output += f"- Increase timeout (current: {timeout}s)\n"
        output += "- Simplify the question\n"
        output += "- Check warehouse status\n"
        return output

    def format_rate_limit(self, question: str, wait_seconds: int) -> str:
        """Format a rate limit message.

        Args:
            question: The original question.
            wait_seconds: Seconds to wait before retry.

        Returns:
            Formatted rate limit markdown.
        """
        output = f"### {question}\n\n"
        output += "⏳ **Rate Limit Reached**\n\n"
        output += f"You've reached the limit of 5 queries per minute. "
        output += f"Please wait {wait_seconds} seconds before trying again.\n"
        return output
