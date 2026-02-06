"""Conversation state tracking for Genie Q&A sessions."""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class ConversationContext:
    """Represents an active Genie conversation."""

    space_id: str
    conversation_id: str
    last_message_id: str
    started_at: datetime
    last_activity: datetime

    def is_expired(self, ttl_minutes: int = 30) -> bool:
        """Check if conversation has expired based on inactivity.

        Args:
            ttl_minutes: Time-to-live in minutes (default: 30).

        Returns:
            True if conversation should be considered expired.
        """
        return datetime.now() - self.last_activity > timedelta(minutes=ttl_minutes)


class ConversationManager:
    """In-memory conversation state tracker for Genie Q&A sessions.

    Tracks active conversations to enable seamless follow-up questions
    without requiring users to manually specify conversation IDs.

    Conversations expire after 30 minutes of inactivity.
    """

    def __init__(self, ttl_minutes: int = 30):
        """Initialize conversation manager.

        Args:
            ttl_minutes: Time-to-live for inactive conversations (default: 30).
        """
        self._conversations: Dict[str, ConversationContext] = {}
        self._ttl_minutes = ttl_minutes

    def get_or_create(
        self,
        space_id: str,
        force_new: bool = False
    ) -> tuple[Optional[str], bool]:
        """Get existing conversation or indicate a new one should be created.

        Args:
            space_id: The Genie space ID.
            force_new: If True, always create a new conversation.

        Returns:
            Tuple of (conversation_id, is_new):
            - If existing conversation found: (conversation_id, False)
            - If new conversation needed: (None, True)
        """
        key = space_id

        # Clean up expired conversations first
        self._cleanup_expired()

        if not force_new and key in self._conversations:
            ctx = self._conversations[key]
            if not ctx.is_expired(self._ttl_minutes):
                return (ctx.conversation_id, False)

        return (None, True)

    def update(
        self,
        space_id: str,
        conversation_id: str,
        message_id: str
    ):
        """Update conversation state after a query.

        Args:
            space_id: The Genie space ID.
            conversation_id: The conversation ID.
            message_id: The message ID from the latest response.
        """
        now = datetime.now()

        # Preserve started_at if conversation already exists
        started_at = now
        if space_id in self._conversations:
            started_at = self._conversations[space_id].started_at

        self._conversations[space_id] = ConversationContext(
            space_id=space_id,
            conversation_id=conversation_id,
            last_message_id=message_id,
            started_at=started_at,
            last_activity=now
        )

    def get_last_space(self) -> Optional[str]:
        """Get the most recently active space ID.

        Returns:
            Space ID or None if no active conversations.
        """
        self._cleanup_expired()

        if not self._conversations:
            return None

        # Return space with most recent activity
        most_recent = max(
            self._conversations.values(),
            key=lambda ctx: ctx.last_activity
        )
        return most_recent.space_id

    def get_context(self, space_id: str) -> Optional[ConversationContext]:
        """Get full conversation context for a space.

        Args:
            space_id: The Genie space ID.

        Returns:
            ConversationContext or None if not found/expired.
        """
        self._cleanup_expired()
        return self._conversations.get(space_id)

    def clear(self, space_id: Optional[str] = None):
        """Clear conversation state.

        Args:
            space_id: If provided, clear only this space. Otherwise clear all.
        """
        if space_id:
            self._conversations.pop(space_id, None)
        else:
            self._conversations.clear()

    def _cleanup_expired(self):
        """Remove expired conversations from memory."""
        expired_keys = [
            key for key, ctx in self._conversations.items()
            if ctx.is_expired(self._ttl_minutes)
        ]
        for key in expired_keys:
            del self._conversations[key]
