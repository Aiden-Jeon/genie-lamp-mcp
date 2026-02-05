"""Response models for API operations."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class SpaceResponse(BaseModel):
    """Response from space creation/update operations."""

    space_id: str = Field(..., description="Unique identifier for the space")
    title: Optional[str] = Field(None, description="Space title")
    description: Optional[str] = Field(None, description="Space description")
    warehouse_id: Optional[str] = Field(None, description="SQL warehouse ID")
    owner_user_id: Optional[str] = Field(None, description="Owner user ID")
    created_timestamp: Optional[int] = Field(None, description="Creation timestamp")
    updated_timestamp: Optional[int] = Field(None, description="Last update timestamp")


class MessageResponse(BaseModel):
    """Response from asking a question to Genie."""

    conversation_id: str = Field(..., description="Unique identifier for the conversation")
    message_id: str = Field(..., description="Unique identifier for the message")
    status: str = Field(..., description="Message status (COMPLETED, EXECUTING_QUERY, FAILED, etc.)")
    response_text: Optional[str] = Field(None, description="Genie's text response")
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    query_result: Optional[dict[str, Any]] = Field(
        None, description="Query results if available"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


class ConversationSummary(BaseModel):
    """Summary of a conversation."""

    conversation_id: str = Field(..., description="Unique identifier for the conversation")
    space_id: str = Field(..., description="Space this conversation belongs to")
    title: Optional[str] = Field(None, description="Conversation title")
    message_count: int = Field(..., description="Number of messages in the conversation")
    created_timestamp: Optional[int] = Field(None, description="Creation timestamp")
    updated_timestamp: Optional[int] = Field(None, description="Last update timestamp")


class TableMetadata(BaseModel):
    """Metadata for a Unity Catalog table."""

    catalog_name: str = Field(..., description="Catalog name")
    schema_name: str = Field(..., description="Schema name")
    table_name: str = Field(..., description="Table name")
    table_type: Optional[str] = Field(None, description="Table type (MANAGED, EXTERNAL, VIEW)")
    comment: Optional[str] = Field(None, description="Table comment/description")
    columns: list[dict[str, Any]] = Field(
        default_factory=list, description="Column metadata (name, type, comment)"
    )
    owner: Optional[str] = Field(None, description="Table owner")
