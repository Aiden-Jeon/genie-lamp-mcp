"""MCP Skills for Genie Lamp Server.

This package provides conversational interfaces (MCP Prompts) that bundle
common workflows into easy-to-use skills for both human users and AI agents.
"""

from genie_mcp_server.skills.utils.conversation_manager import ConversationManager

# Global conversation manager instance
conversation_manager = ConversationManager()

__all__ = [
    "conversation_manager",
]
