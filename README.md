# Databricks Genie MCP Server

A comprehensive Model Context Protocol (MCP) server for Databricks Genie that enables:
- **Space Management** - Create, update, list, and delete Genie spaces
- **Conversational Queries** - Ask questions and get SQL results with automatic polling
- **LLM-Powered Config Generation** - Generate Genie space configurations from natural language requirements

## Features

### Space Management (5 tools)
- `create_genie_space` - Create a new Genie space from JSON configuration
- `list_genie_spaces` - List all Genie spaces in the workspace
- `get_genie_space` - Get details of a specific space
- `update_genie_space` - Update an existing space
- `delete_genie_space` - Delete a space (soft delete)

### Conversation/Query (5 tools)
- `ask_genie` - Ask a question and wait for results (with rate limiting and polling)
- `continue_conversation` - Send a follow-up question in an existing conversation
- `get_query_results` - Fetch query results from a completed message
- `list_conversations` - List conversations in a space
- `get_conversation_history` - Get all messages in a conversation thread

### Configuration Generation (3 tools)
- `generate_space_config` - Generate a complete Genie space config from natural language
- `validate_space_config` - Validate a configuration for errors and quality
- `extract_table_metadata` - Extract Unity Catalog table metadata for context

## Installation

### Prerequisites
- Python 3.10 or higher
- Databricks workspace with Genie enabled
- SQL warehouse ID
- Authentication credentials (PAT or OAuth M2M)

### Install from source

```bash
# Clone the repository
cd genie-mcp-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
pip install -e .

# For development
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your Databricks credentials:

```env
# Required
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com

# Choose one authentication method:
# Option 1: Personal Access Token
DATABRICKS_TOKEN=dapi...

# Option 2: OAuth M2M Service Principal
# DATABRICKS_CLIENT_ID=your-client-id
# DATABRICKS_CLIENT_SECRET=your-client-secret

# Option 3: Omit both to use Databricks CLI default auth

# Optional
DATABRICKS_TIMEOUT_SECONDS=300
DATABRICKS_POLL_INTERVAL_SECONDS=2
DATABRICKS_SERVING_ENDPOINT_NAME=databricks-dbrx-instruct
```

## Running the Server

### Standalone

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the server
genie-mcp-server
```

The server will start and communicate via stdio (standard input/output).

### With Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "genie": {
      "command": "/path/to/genie-mcp-server/.venv/bin/python",
      "args": ["-m", "genie_mcp_server.server"],
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.cloud.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

Restart Claude Desktop and the tools will be available.

## Usage Examples

### Space Management

**Create a space:**
```python
# Use the create_genie_space tool with JSON config
config = {
    "space_name": "Sales Analytics",
    "description": "Natural language queries for sales data",
    "tables": [
        {
            "catalog_name": "main",
            "schema_name": "sales",
            "table_name": "transactions"
        }
    ],
    "instructions": [
        {
            "content": "Use `transaction_date` for date filtering",
            "priority": 1
        }
    ]
}

create_genie_space(
    warehouse_id="abc123",
    serialized_space=json.dumps(config),
    title="Sales Analytics"
)
```

**List spaces:**
```python
list_genie_spaces(page_size=10)
```

### Conversational Queries

**Ask a question:**
```python
# Automatically handles rate limiting and polling
result = await ask_genie(
    space_id="01ef...",
    question="What were the top 10 selling products last week?",
    timeout_seconds=300
)

# Result includes: conversation_id, message_id, response_text, sql_query, query_result
```

**Continue conversation:**
```python
result = await continue_conversation(
    space_id="01ef...",
    conversation_id="conv123",
    question="Show me the revenue for those products"
)
```

### Configuration Generation

**Generate config from requirements:**
```python
result = generate_space_config(
    requirements="""
    Create a Genie space for analyzing customer orders.
    - Track order trends over time
    - Analyze customer segments
    - Monitor revenue and product performance
    Tables: main.sales.orders, main.sales.customers, main.sales.products
    """,
    warehouse_id="abc123",
    catalog_name="main"
)

# Result includes: genie_space_config, reasoning, confidence_score, validation_report
```

**Validate a configuration:**
```python
result = validate_space_config(
    config=json.dumps(config_dict),
    validate_sql=True
)

# Result includes: valid, errors, warnings, score (0-100)
```

**Extract table metadata:**
```python
metadata = extract_table_metadata(
    catalog_name="main",
    schema_name="sales",
    table_names=["orders", "customers"]
)

# Use metadata as context for config generation
```

## Architecture

```
MCP Server (stdio)
├── Space Management Tools (CRUD via Databricks SDK)
├── Conversation Tools (async polling, rate limiting)
└── Config Generation Tools (LLM-powered via serving endpoints)
```

### Key Components

- **fastmcp** - Python MCP framework with decorator-based tools
- **Databricks SDK** - Official Python SDK for API access
- **Pydantic** - Data validation and settings management
- **sqlparse** - SQL syntax validation
- **asyncio** - Async polling for long-running queries

### Rate Limiting

Genie API limits: **5 queries per minute** (Public Preview)

The server automatically:
- Tracks requests in a sliding window
- Blocks when limit reached
- Waits until window slides

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

### Project Structure

```
genie-mcp-server/
├── src/genie_mcp_server/
│   ├── server.py                      # Main MCP server entry point
│   ├── config.py                      # Configuration management
│   ├── auth.py                        # Databricks authentication
│   ├── tools/
│   │   ├── space_tools.py            # Space CRUD operations
│   │   ├── conversation_tools.py     # Query/conversation tools
│   │   └── config_gen_tools.py       # Config generation tools
│   ├── client/
│   │   ├── genie_client.py           # Databricks API wrapper
│   │   └── polling.py                # Async polling utilities
│   ├── generators/
│   │   ├── space_config_generator.py # LLM config generation
│   │   ├── validator.py              # Config validation
│   │   └── prompts.py                # LLM prompt templates
│   ├── models/
│   │   ├── space.py                  # Pydantic models
│   │   └── responses.py              # API response models
│   └── utils/
│       ├── error_handling.py         # Error translation
│       └── rate_limiter.py           # Rate limiting
├── tests/
├── examples/
├── pyproject.toml
└── README.md
```

## API Reference

See [TOOLS.md](TOOLS.md) for detailed tool documentation.

## Troubleshooting

### Authentication Errors

```
AuthenticationError: Authentication failed
```

**Solution**: Check your credentials in `.env`:
- Verify `DATABRICKS_HOST` is correct
- Ensure `DATABRICKS_TOKEN` is valid (or CLIENT_ID/SECRET)
- Test with `databricks workspace ls /` using the CLI

### Rate Limit Errors

```
RateLimitError: Rate limit exceeded
```

**Solution**: Genie allows 5 queries/minute. Wait 60 seconds or reduce query frequency.

### Timeout Errors

```
TimeoutError: Operation timed out after 300 seconds
```

**Solution**: Increase `timeout_seconds` parameter for complex queries.

### Space Not Found

```
SpaceNotFoundError: Resource not found
```

**Solution**: Verify the space_id exists with `list_genie_spaces`.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

Apache License 2.0

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/databricks-field-eng/genie-mcp-server/issues)
- Documentation: [Databricks Genie Docs](https://docs.databricks.com/genie/)

## References

- [Databricks Genie API](https://docs.databricks.com/api/workspace/genie)
- [Genie Conversation API](https://docs.databricks.com/aws/en/genie/conversation-api)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [fastmcp](https://github.com/jlowin/fastmcp)
- [Databricks SDK Python](https://docs.databricks.com/dev-tools/sdk-python)
