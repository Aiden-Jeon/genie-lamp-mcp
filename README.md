# Databricks Genie MCP Server

A comprehensive Model Context Protocol (MCP) server for Databricks Genie that enables:
- **Space Management** - Create, update, list, and delete Genie spaces
- **Conversational Queries** - Ask questions and get SQL results with automatic polling
- **LLM-Powered Config Generation** - Generate Genie space configurations from natural language requirements

## Quick Start

Get started in 5 minutes:

### Prerequisites

- Python 3.10 or higher
- Databricks workspace with Genie enabled
- SQL warehouse ID
- Authentication credentials (PAT or OAuth M2M)

### Quick Install

Use the automated installation script:

```bash
# Clone the repository
cd genie-mcp-server

# Run the install script (handles everything)
./install.sh
```

The script will:
- Check Python version
- Create virtual environment
- Install dependencies
- Interactively configure Databricks authentication
- Auto-detect and select from your Databricks CLI profiles
- Set up .env configuration file
- Verify installation

### Quick Configure

If already installed, configure anytime:

```bash
./configure.sh
```

This will interactively guide you through:
- Selecting authentication method (CLI/PAT/OAuth)
- Entering workspace URL
- Setting up credentials
- Configuring timeouts and endpoints

### Test & Verify

```bash
# Activate virtual environment
source .venv/bin/activate

# Check imports
python -c "from genie_mcp_server import config; print('✓ Config OK')"
```

### First Query

After setup, ask Claude:
> "List all Genie spaces in my workspace"

Claude will use the `list_genie_spaces` tool automatically.

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

**Key Capabilities:**
- Automatic rate limiting (5 requests/minute)
- Async polling for long-running queries
- Multi-layer configuration validation
- LLM-powered config generation via serving endpoints

## Installation

### Quick Install (Recommended)

Use the automated installation script:

```bash
# Clone the repository
cd genie-mcp-server

# Run the install script
./install.sh
```

The script handles: Python version check, virtual environment creation, dependency installation, and interactive configuration setup with Databricks CLI profile detection.

### Manual Install

If you prefer manual installation:

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

# Copy environment template
cp .env.example .env
```

### Non-Interactive Setup

For CI/CD or automated setups, create `.env` before running:

```bash
cat > .env << EOF
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
# CLI auth - no token needed
DATABRICKS_TIMEOUT_SECONDS=300
DATABRICKS_POLL_INTERVAL_SECONDS=2
DATABRICKS_MAX_RETRIES=3
DATABRICKS_SERVING_ENDPOINT_NAME=databricks-dbrx-instruct
EOF

./install.sh
```

## Configuration

### Interactive Configuration (Recommended)

Use the configuration script for guided setup:

```bash
./configure.sh
```

The script will:
- Detect Databricks CLI and offer to use its authentication
- Interactively prompt for workspace URL and credentials
- Set up all configuration options with sensible defaults
- Validate authentication if using Databricks CLI
- Backup existing `.env` to `.env.backup` before changes

### Manual Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your Databricks credentials:

```env
# Required
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com

# Choose one authentication method:
# Option 1: Databricks CLI (recommended - no credentials needed)
# Install: pip install databricks-cli
# Authenticate: databricks auth login
# Then omit DATABRICKS_TOKEN and CLIENT credentials below

# Option 2: Personal Access Token
DATABRICKS_TOKEN=dapi...

# Option 3: OAuth M2M Service Principal
# DATABRICKS_CLIENT_ID=your-client-id
# DATABRICKS_CLIENT_SECRET=your-client-secret

# Optional
DATABRICKS_TIMEOUT_SECONDS=300
DATABRICKS_POLL_INTERVAL_SECONDS=2
DATABRICKS_SERVING_ENDPOINT_NAME=databricks-dbrx-instruct
```

### Authentication Methods

**Databricks CLI (Recommended)**
- No credentials in `.env` file
- Uses your existing Databricks authentication
- Supports SSO, MFA, and multiple profiles
- Automatic token refresh
- Setup: `pip install databricks-cli && databricks auth login`

**Personal Access Token**
- Simple to set up
- Good for development
- Generate in Databricks workspace: User Settings → Access Tokens
- Add to `.env`: `DATABRICKS_TOKEN=dapi...`

**OAuth M2M Service Principal**
- For production/automated workflows
- Fine-grained permissions and audit logging
- Requires service principal setup in Databricks
- Add to `.env`: `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET`

## Usage with Claude Desktop

### Configuration File Location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Add MCP Server

Edit the configuration file:

```json
{
  "mcpServers": {
    "genie": {
      "command": "/absolute/path/to/genie-mcp-server/.venv/bin/python",
      "args": ["-m", "genie_mcp_server.server"],
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.cloud.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

### Restart and Verify

1. Restart Claude Desktop
2. Verify tools are available - you should see 13 Genie tools in Claude
3. Test with: "List all Genie spaces in my workspace"

## API Reference

### Summary of Tools

| Tool | Category | Description |
|------|----------|-------------|
| `create_genie_space` | Space Management | Create a new Genie space from JSON configuration |
| `list_genie_spaces` | Space Management | List all Genie spaces in the workspace |
| `get_genie_space` | Space Management | Get details of a specific space |
| `update_genie_space` | Space Management | Update an existing space |
| `delete_genie_space` | Space Management | Delete a space (soft delete) |
| `ask_genie` | Conversation/Query | Ask a question and wait for results (with rate limiting) |
| `continue_conversation` | Conversation/Query | Send a follow-up question in an existing conversation |
| `get_query_results` | Conversation/Query | Fetch query results from a completed message |
| `list_conversations` | Conversation/Query | List conversations in a space |
| `get_conversation_history` | Conversation/Query | Get all messages in a conversation thread |
| `generate_space_config` | Config Generation | Generate a complete Genie space config from natural language |
| `validate_space_config` | Config Generation | Validate a configuration for errors and quality |
| `extract_table_metadata` | Config Generation | Extract Unity Catalog table metadata for context |

<details>
<summary>Detailed Tool Documentation (click to expand)</summary>

### Space Management Tools

#### create_genie_space
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

#### list_genie_spaces
List all Genie spaces in the workspace.

**Parameters:**
- `page_size` (int, optional): Number of spaces to return per page
- `page_token` (string, optional): Token for pagination

**Returns:** JSON with array of space summaries and optional `next_page_token`

#### get_genie_space
Get details of a specific Genie space.

**Parameters:**
- `space_id` (string, required): Unique identifier for the space
- `include_config` (bool, optional): Whether to include full configuration (default: true)

**Returns:** JSON with space details including configuration if requested

#### update_genie_space
Update an existing Genie space.

**Parameters:**
- `space_id` (string, required): Unique identifier for the space
- `serialized_space` (string, optional): New JSON configuration
- `title` (string, optional): New title
- `description` (string, optional): New description
- `warehouse_id` (string, optional): New SQL warehouse ID

**Returns:** JSON with updated space details

#### delete_genie_space
Delete a Genie space (soft delete - moves to trash).

**Parameters:**
- `space_id` (string, required): Unique identifier for the space to delete

**Returns:** JSON with success confirmation

### Conversation/Query Tools

#### ask_genie
Ask a question to Genie and wait for the response. Automatically applies rate limiting (5 queries per minute) and polls until the query completes or times out.

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

#### continue_conversation
Continue an existing conversation with a follow-up question.

**Parameters:**
- `space_id` (string, required): Unique identifier for the Genie space
- `conversation_id` (string, required): ID of the conversation to continue
- `question` (string, required): Follow-up question
- `timeout_seconds` (int, optional): Maximum time to wait (default: 300)
- `poll_interval_seconds` (int, optional): Time between checks (default: 2)

**Returns:** JSON with message details and results (same format as `ask_genie`)

#### get_query_results
Fetch query result data from a completed message.

**Parameters:**
- `space_id` (string, required): Unique identifier for the Genie space
- `conversation_id` (string, required): ID of the conversation
- `message_id` (string, required): ID of the message with query results
- `attachment_id` (string, optional): Optional specific attachment ID

**Returns:** JSON with query results (up to 5,000 rows)

#### list_conversations
List conversations in a Genie space.

**Parameters:**
- `space_id` (string, required): Unique identifier for the Genie space
- `page_size` (int, optional): Number of conversations to return (default: 50)
- `page_token` (string, optional): Token for pagination

**Returns:** JSON with conversation summaries

#### get_conversation_history
Get all messages in a conversation.

**Parameters:**
- `space_id` (string, required): Unique identifier for the Genie space
- `conversation_id` (string, required): ID of the conversation

**Returns:** JSON with complete conversation thread

### Configuration Generation Tools

#### generate_space_config
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

#### validate_space_config
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

**Score Breakdown:**
- 90-100: Excellent configuration
- 80-89: Good configuration with minor improvements
- 70-79: Acceptable with some warnings
- 60-69: Needs improvement
- <60: Significant issues

#### extract_table_metadata
Extract metadata for Unity Catalog tables. This metadata can be used as context when generating configurations.

**Parameters:**
- `catalog_name` (string, required): Catalog name in Unity Catalog
- `schema_name` (string, required): Schema name in Unity Catalog
- `table_names` (list[string], optional): Specific table names to include (default: all tables in schema)

**Returns:** JSON with table metadata including columns, types, and descriptions

</details>

## Usage Examples

### Space Management

**List spaces:**
```
List all Genie spaces
```

**Get space details:**
```
Get details for space ID 01ef...
```

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

In Claude Desktop:
```
Ask space [space_id]: "What were total sales last month?"
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

**Generate config:**
```
Generate a Genie space config for analyzing sales data. Use tables from main.sales schema: orders, customers, products
```

**Validate config:**
```
Validate this Genie space configuration: [config]
```

**Generate config from requirements (programmatic):**
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

## Troubleshooting

### Authentication Errors

```
AuthenticationError: Authentication failed
```

**Solution**: Check your credentials in `.env`:
- Verify `DATABRICKS_HOST` is correct (including https://)
- Ensure `DATABRICKS_TOKEN` is valid (or CLIENT_ID/SECRET)
- Test with `databricks workspace ls /` using the CLI

### Module Not Found

```
ModuleNotFoundError: No module named 'genie_mcp_server'
```

**Solution**:
- Ensure virtual environment is activated
- Re-run: `pip install -e .`

### Rate Limit Errors

```
RateLimitError: Rate limit exceeded
```

**Solution**: Genie allows 5 queries/minute. Wait 60 seconds or reduce query frequency. Tools automatically handle rate limiting.

### Timeout Errors

```
TimeoutError: Operation timed out after 300 seconds
```

**Solution**: Increase `timeout_seconds` parameter for complex queries or set in `.env`: `DATABRICKS_TIMEOUT_SECONDS=600`

### Space Not Found

```
SpaceNotFoundError: Resource not found
```

**Solution**: Verify the space_id exists with `list_genie_spaces`.

### Profile Issues (CLI Auth)

**No profiles found:**
```bash
# Authenticate with Databricks CLI
databricks auth login
./configure.sh
```

**Profile shows (not configured):**
```bash
# Configure the profile
databricks auth login --profile YOUR_PROFILE_NAME
```

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
