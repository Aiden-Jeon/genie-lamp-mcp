# MCP Tools Documentation

This document provides detailed documentation for all 13 MCP tools provided by the Genie MCP Server.

## Space Management Tools (5)

### 1. create_genie_space

Create a new Genie space from JSON configuration.

**Parameters:**
- `warehouse_id` (string, required): SQL warehouse ID for query execution
- `serialized_space` (string, required): JSON string containing space configuration
- `title` (string, optional): Space title
- `description` (string, optional): Space description
- `parent_path` (string, optional): Parent path in workspace

**Returns:** JSON with created space details including `space_id`

**Example:**
```json
{
  "space_id": "01ef...",
  "title": "Sales Analytics",
  "warehouse_id": "abc123",
  "created_timestamp": 1234567890
}
```

---

### 2. list_genie_spaces

List all Genie spaces in the workspace.

**Parameters:**
- `page_size` (int, optional): Number of spaces to return per page
- `page_token` (string, optional): Token for pagination

**Returns:** JSON with array of space summaries and optional `next_page_token`

**Example:**
```json
{
  "spaces": [
    {
      "space_id": "01ef...",
      "title": "Sales Analytics",
      "description": "Natural language queries for sales data",
      "warehouse_id": "abc123"
    }
  ],
  "next_page_token": null
}
```

---

### 3. get_genie_space

Get details of a specific Genie space.

**Parameters:**
- `space_id` (string, required): Unique identifier for the space
- `include_config` (bool, optional): Whether to include full configuration (default: true)

**Returns:** JSON with space details including configuration if requested

**Example:**
```json
{
  "space_id": "01ef...",
  "title": "Sales Analytics",
  "description": "Natural language queries for sales data",
  "warehouse_id": "abc123",
  "serialized_space": "{...}"
}
```

---

### 4. update_genie_space

Update an existing Genie space.

**Parameters:**
- `space_id` (string, required): Unique identifier for the space
- `serialized_space` (string, optional): New JSON configuration
- `title` (string, optional): New title
- `description` (string, optional): New description
- `warehouse_id` (string, optional): New SQL warehouse ID

**Returns:** JSON with updated space details

---

### 5. delete_genie_space

Delete a Genie space (soft delete - moves to trash).

**Parameters:**
- `space_id` (string, required): Unique identifier for the space to delete

**Returns:** JSON with success confirmation

**Example:**
```json
{
  "status": "success",
  "message": "Space 01ef... deleted successfully"
}
```

---

## Conversation/Query Tools (5)

### 6. ask_genie

Ask a question to Genie and wait for the response. This tool automatically applies rate limiting (5 queries per minute) and polls until the query completes or times out.

**Parameters:**
- `space_id` (string, required): Unique identifier for the Genie space
- `question` (string, required): Natural language question to ask
- `timeout_seconds` (int, optional): Maximum time to wait for response (default: 300)
- `poll_interval_seconds` (int, optional): Time between status checks (default: 2)

**Returns:** JSON with conversation details, response, SQL query, and results

**Example:**
```json
{
  "conversation_id": "conv123",
  "message_id": "msg456",
  "status": "COMPLETED",
  "response_text": "Here are the top 10 selling products...",
  "sql_query": "SELECT product_name, COUNT(*) as sales FROM...",
  "query_result": {
    "rows": [...],
    "row_count": 10,
    "schema": [...]
  }
}
```

---

### 7. continue_conversation

Continue an existing conversation with a follow-up question.

**Parameters:**
- `space_id` (string, required): Unique identifier for the Genie space
- `conversation_id` (string, required): ID of the conversation to continue
- `question` (string, required): Follow-up question
- `timeout_seconds` (int, optional): Maximum time to wait (default: 300)
- `poll_interval_seconds` (int, optional): Time between checks (default: 2)

**Returns:** JSON with message details and results (same format as `ask_genie`)

---

### 8. get_query_results

Fetch query result data from a completed message.

**Parameters:**
- `space_id` (string, required): Unique identifier for the Genie space
- `conversation_id` (string, required): ID of the conversation
- `message_id` (string, required): ID of the message with query results
- `attachment_id` (string, optional): Optional specific attachment ID

**Returns:** JSON with query results (up to 5,000 rows)

**Example:**
```json
{
  "rows": [[val1, val2, ...], ...],
  "row_count": 100,
  "schema": [
    {"name": "product_name", "type": "STRING"},
    {"name": "sales", "type": "INTEGER"}
  ]
}
```

---

### 9. list_conversations

List conversations in a Genie space.

**Parameters:**
- `space_id` (string, required): Unique identifier for the Genie space
- `page_size` (int, optional): Number of conversations to return (default: 50)
- `page_token` (string, optional): Token for pagination

**Returns:** JSON with conversation summaries

**Example:**
```json
{
  "conversations": [
    {
      "conversation_id": "conv123",
      "space_id": "01ef...",
      "title": "Sales Analysis",
      "created_timestamp": 1234567890
    }
  ],
  "next_page_token": null
}
```

---

### 10. get_conversation_history

Get all messages in a conversation.

**Parameters:**
- `space_id` (string, required): Unique identifier for the Genie space
- `conversation_id` (string, required): ID of the conversation

**Returns:** JSON with complete conversation thread

**Example:**
```json
{
  "conversation_id": "conv123",
  "space_id": "01ef...",
  "title": "Sales Analysis",
  "messages": [
    {
      "message_id": "msg1",
      "content": "What were the top selling products?",
      "status": "COMPLETED",
      "created_timestamp": 1234567890
    }
  ]
}
```

---

## Configuration Generation Tools (3)

### 11. generate_space_config

Generate a complete Genie space configuration from natural language requirements using an LLM. The generated configuration is automatically validated before being returned.

**Parameters:**
- `requirements` (string, required): Natural language description of desired Genie space
- `warehouse_id` (string, required): SQL warehouse ID for query execution
- `catalog_name` (string, required): Unity Catalog name to use
- `serving_endpoint_name` (string, optional): Serving endpoint name (uses default if not provided)
- `validate_sql` (bool, optional): Whether to validate SQL syntax (default: true)

**Returns:** JSON with generated configuration, reasoning, confidence score, and validation report

**Example Input:**
```
Create a Genie space for analyzing customer orders.
- Track order trends over time
- Analyze customer segments
- Monitor revenue and product performance
Tables: main.sales.orders, main.sales.customers
```

**Example Output:**
```json
{
  "genie_space_config": {
    "space_name": "Customer Order Analytics",
    "description": "...",
    "tables": [...],
    "instructions": [...],
    "example_sql_queries": [...]
  },
  "reasoning": "This configuration focuses on...",
  "confidence_score": 0.95,
  "validation_report": {
    "valid": true,
    "errors": [],
    "warnings": ["Consider adding more example queries"],
    "score": 85
  }
}
```

---

### 12. validate_space_config

Validate a Genie space configuration using multi-layer validation.

**Validation Layers:**
1. Schema validation (Pydantic model)
2. SQL syntax validation (sqlparse)
3. Instruction quality scoring
4. Completeness check

**Parameters:**
- `config` (string, required): JSON string containing Genie space configuration
- `validate_sql` (bool, optional): Whether to validate SQL syntax (default: true)
- `catalog_name` (string, optional): Catalog name for context

**Returns:** JSON with validation results

**Example:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Instruction #2 is very short (8 words)",
    "No example SQL queries - consider adding examples"
  ],
  "score": 75
}
```

**Score Breakdown:**
- 90-100: Excellent configuration
- 80-89: Good configuration with minor improvements
- 70-79: Acceptable with some warnings
- 60-69: Needs improvement
- <60: Significant issues

---

### 13. extract_table_metadata

Extract metadata for Unity Catalog tables. This metadata can be used as context when generating configurations.

**Parameters:**
- `catalog_name` (string, required): Catalog name in Unity Catalog
- `schema_name` (string, required): Schema name in Unity Catalog
- `table_names` (list[string], optional): Specific table names to include (default: all tables in schema)

**Returns:** JSON with table metadata including columns, types, and descriptions

**Example:**
```json
{
  "catalog_name": "main",
  "schema_name": "sales",
  "tables": [
    {
      "catalog_name": "main",
      "schema_name": "sales",
      "table_name": "orders",
      "table_type": "MANAGED",
      "comment": "Customer order transactions",
      "columns": [
        {
          "name": "order_id",
          "type": "BIGINT",
          "comment": "Unique order identifier"
        },
        {
          "name": "customer_id",
          "type": "BIGINT",
          "comment": "Customer identifier"
        },
        {
          "name": "order_date",
          "type": "DATE",
          "comment": "Order date"
        }
      ],
      "owner": "user@example.com"
    }
  ]
}
```

---

## Rate Limiting

The `ask_genie` and `continue_conversation` tools automatically apply rate limiting to respect Genie API limits:

- **Limit**: 5 queries per minute (Public Preview)
- **Behavior**: Tools will automatically wait if limit is reached
- **Window**: Sliding 60-second window

---

## Error Handling

All tools translate Databricks SDK errors into user-friendly messages:

- `AuthenticationError`: Check your credentials in `.env`
- `SpaceNotFoundError`: Verify the space_id exists
- `RateLimitError`: Wait 60 seconds or reduce query frequency
- `TimeoutError`: Increase `timeout_seconds` parameter
- `ValidationError`: Check configuration format and content
- `LLMError`: Check serving endpoint name and availability

---

## Best Practices

### Space Configuration
1. Use specific column/table names in instructions (with backticks)
2. Provide 3-5 example SQL queries covering different patterns
3. Add SQL snippets (filters, expressions, measures) for reusability
4. Include meaningful descriptions and instructions
5. Use markdown formatting for readability

### Querying
1. Start with simple questions to test the space
2. Use follow-up questions to refine results
3. Set appropriate `timeout_seconds` for complex queries
4. Check conversation history to understand context

### Configuration Generation
1. Provide detailed requirements with specific use cases
2. Extract table metadata first for better context
3. Validate generated configs before deployment
4. Review and refine based on validation warnings
5. Test with benchmark questions after deployment
