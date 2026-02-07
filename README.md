# Databricks Genie MCP Server

A comprehensive Model Context Protocol (MCP) server for Databricks Genie that enables:
- **Space Management** - Create, update, list, and delete Genie spaces
- **Conversational Queries** - Ask questions and get SQL results with automatic polling
- **AI-Friendly Config Schema** - Discoverable JSON schema and templates for AI assistants to generate valid configurations
- **Conversational Skills** - High-level workflows with guided setup, smart conversation tracking, and health monitoring

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
python -c "from genie_mcp_server import config; print('Config OK')"
```

### First Query

After setup, ask Claude:
> "List all Genie spaces in my workspace"

Claude will use the `list_genie_spaces` tool automatically.

## Features

### Conversational Skills (4 prompts)

High-level workflows that bundle common operations into easy-to-use conversational interfaces:

- **`/create-space`** - Guided space creation with auto-warehouse discovery and validation feedback
  - Quick mode (instant creation), Guided mode (validation feedback), Expert mode (manual editing)
  - Domain templates (minimal, sales, customer, inventory, financial, hr)
  - Quality scoring and recommendations

- **`/ask`** - Natural Q&A with automatic conversation tracking
  - Smart space selection (by ID, name, or last-used)
  - 30-minute conversation continuity (no need to track conversation IDs)
  - Adaptive result formatting (tables, summaries, SQL)
  - Rate limit and timeout handling

- **`/inspect`** - Space analysis and configuration management
  - Health check (config quality + activity metrics)
  - Export (save config as JSON for backup/cloning)
  - Diff (compare two spaces side-by-side)
  - Find (search spaces by table or keyword)

- **`/bulk`** - Batch operations on multiple spaces
  - Update (add instructions/tables to multiple spaces)
  - Delete (pattern matching with dry-run preview)
  - Dry-run mode for safety

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

### Configuration Generation (5 tools)
- `get_config_schema` - Get JSON schema and documentation for creating configs
- `get_config_template` - Get domain-specific config templates (sales, customer, inventory, etc.)
- `validate_space_config` - Validate a configuration for errors and quality
- `extract_table_metadata` - Extract Unity Catalog table metadata for context
- `generate_space_config` - (Deprecated) Legacy LLM-based generation

**Key Capabilities:**
- Automatic rate limiting (5 requests/minute)
- Async polling for long-running queries
- Multi-layer configuration validation
- Schema-driven config generation for AI assistants (no external endpoint needed)

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
DATABRICKS_MAX_RETRIES=3
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
- Generate in Databricks workspace: User Settings > Access Tokens
- Add to `.env`: `DATABRICKS_TOKEN=dapi...`

**OAuth M2M Service Principal**
- For production/automated workflows
- Fine-grained permissions and audit logging
- Requires service principal setup in Databricks
- Add to `.env`: `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET`

## Usage with Claude Desktop / Claude Code

### Configuration File Location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Claude Code**: `~/.claude/claude_code_config.json` (or use `claude mcp add`)

### Option 1: uvx (Recommended)

No local clone or virtual environment needed. Just add to your config:

**From git URL:**

```json
{
  "mcpServers": {
    "genie": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/Aiden-Jeon/genie-lamp-mcp.git", "genie-mcp-server"],
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.cloud.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

**If published to PyPI:**

```json
{
  "mcpServers": {
    "genie": {
      "command": "uvx",
      "args": ["genie-mcp-server"],
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.cloud.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

### Option 2: Local venv (for development)

If you cloned the repo and installed locally:

```json
{
  "mcpServers": {
    "genie": {
      "command": "/absolute/path/to/genie-lamp-mcp/.venv/bin/genie-mcp-server",
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.cloud.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

### Restart and Verify

1. Restart Claude Desktop (or reload Claude Code)
2. Verify tools are available - you should see 15 Genie tools in Claude
3. Test with: "List all Genie spaces in my workspace"

## Skills Usage Guide

### `/create-space` - Space Creation Wizard

**Basic Usage** - Create a space with automatic warehouse discovery:

```python
create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders,customers,products"
)
```

**Quick Mode** - Skip validation and create immediately:

```python
create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders",
    domain="sales",
    quick=True
)
```

**Expert Mode** - Get the configuration JSON for manual editing:

```python
create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders",
    expert=True
)
```

**With Custom Settings:**

```python
create_space(
    catalog_name="main",
    schema_name="finance",
    table_names="transactions,accounts,invoices",
    warehouse_id="581ed75401284b97",
    domain="financial",
    space_name="Q4 Financial Analytics"
)
```

**Available Domains:** `minimal` (default), `sales`, `customer`, `inventory`, `financial`, `hr`

### `/ask` - Q&A Assistant

**Basic Usage:**

```python
ask(
    question="What is the total revenue for last month?",
    space_id="01234567-89ab-cdef-0123-456789abcdef"
)
```

**By Space Name:**

```python
ask(
    question="Show top 10 customers by revenue",
    space_name="Sales Analytics"
)
```

**Follow-up Questions** - The skill automatically continues conversations:

```python
# First question (starts new conversation)
ask(question="What is total revenue?", space_id="abc123")

# Follow-up (continues same conversation automatically)
ask(question="Show breakdown by product category")

# Another follow-up (still same conversation)
ask(question="Filter to last quarter only")
```

**Start New Conversation:**

```python
ask(
    question="Different topic: show inventory levels",
    space_id="abc123",
    new_conversation=True
)
```

**Verbose Mode** - Show all rows (not just top 10):

```python
ask(question="List all products", space_id="abc123", verbose=True)
```

**Custom Timeout** - For complex queries:

```python
ask(question="Complex aggregation", space_id="abc123", timeout=600)
```

### `/inspect` - Space Inspector

**Health Check** - Analyze space configuration and activity:

```python
inspect(space_id="abc123", mode="health")
```

Output includes: Overall health score (0-100), configuration metrics, activity metrics, actionable recommendations.

**Export Configuration:**

```python
inspect(space_id="abc123", mode="export")
inspect(space_id="abc123", mode="export", output_file="config.json")
```

**Compare Spaces:**

```python
inspect(space_id="abc123", mode="diff", compare_with="def456")
```

**Find Spaces** by table or keyword:

```python
inspect(space_id="", mode="find", search_tables="orders,customers")
inspect(space_id="", mode="find", search_keywords="sales,revenue")
```

### `/bulk` - Bulk Operations

**Update Multiple Spaces:**

```python
# Dry run first (preview changes)
bulk(
    operation="update",
    space_ids="abc123,def456,ghi789",
    add_instructions="Always use fiscal year dates",
    dry_run=True
)

# Apply changes
bulk(
    operation="update",
    space_ids="abc123,def456,ghi789",
    add_instructions="Always use fiscal year dates",
    dry_run=False
)
```

**Delete Multiple Spaces:**

```python
# By explicit IDs (dry run first)
bulk(operation="delete", space_ids="test1,test2,test3", dry_run=True)

# By pattern matching
bulk(operation="delete", pattern="test-*", dry_run=True)
bulk(operation="delete", pattern="*-dev", dry_run=True)
bulk(operation="delete", pattern="*staging*", dry_run=True)
```

> **Warning:** Always use `dry_run=True` first to preview deletions!

### Common Workflows

**Create and Validate a Space:**

```python
# 1. Create space with guided mode
create_space(catalog_name="main", schema_name="sales", table_names="orders,customers", domain="sales")

# 2. Check health
inspect(space_id="<space_id>", mode="health")

# 3. Test with questions
ask(question="What tables are available?", space_id="<space_id>")
```

**Clone and Modify a Space:**

```python
# 1. Export existing space config
inspect(space_id="original-space-id", mode="export", output_file="original_config.json")

# 2. Edit the config file manually

# 3. Create new space with modified config using create_genie_space tool
```

**Batch Space Management:**

```python
# 1. Find all spaces using a specific table
inspect(space_id="", mode="find", search_tables="main.sales.transactions")

# 2. Add common instruction to all found spaces
bulk(operation="update", space_ids="space1,space2,space3", add_instructions="Always filter to last 365 days", dry_run=True)

# 3. Verify changes
inspect(space_id="space1", mode="health")
```

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
| `get_config_schema` | Config Generation | Get JSON schema and documentation for creating configs |
| `get_config_template` | Config Generation | Get domain-specific config templates |
| `validate_space_config` | Config Generation | Validate a configuration for errors and quality |
| `extract_table_metadata` | Config Generation | Extract Unity Catalog table metadata for context |
| `generate_space_config` | Config Generation | (Deprecated) Legacy LLM-based generation |

<details>
<summary>Detailed Tool Documentation (click to expand)</summary>

### Space Management Tools

#### create_genie_space
Create a new Genie space from GenieSpaceConfig JSON.

This is the final step in the configuration workflow:
1. `get_config_schema` - Get JSON schema for validation
2. `get_config_template` - Get domain-specific template (optional)
3. `validate_space_config` - Validate your configuration
4. `create_genie_space` - Create the space (THIS TOOL)

**Parameters:**
- `warehouse_id` (string, required): SQL warehouse ID for query execution
- `config_json` (string, required): JSON string with GenieSpaceConfig (instructions, tables, examples, SQL snippets)
- `title` (string, optional): Space title (defaults to config.space_name)
- `description` (string, optional): Space description (defaults to config.description)
- `parent_path` (string, optional): Parent path in workspace

**Returns:** JSON with created space details including `space_id`

**Note:** The config is automatically converted to Databricks Protobuf format internally. The configuration includes:
- Tables to include in the space
- Plain text instructions for Genie AI
- Example SQL queries
- SQL snippets (measures, expressions, filters)
- Join specifications between tables
- Benchmark questions for testing

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
- `include_config` (bool, optional): Whether to include full Protobuf configuration (default: false)

**Returns:** JSON with space details

**Note:** When `include_config=true`, the `serialized_space` field contains Databricks Protobuf format with data_sources (tables), sample_questions, and text_instructions.

#### update_genie_space
Update an existing Genie space.

**Parameters:**
- `space_id` (string, required): Unique identifier for the space
- `config_json` (string, optional): New GenieSpaceConfig as JSON string
- `title` (string, optional): New title
- `description` (string, optional): New description
- `warehouse_id` (string, optional): New SQL warehouse ID

**Returns:** JSON with updated space details

**Note:** Use the same GenieSpaceConfig format as `create_genie_space`.

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

#### get_config_schema
Get the JSON schema and documentation for Genie space configurations. This is the recommended way for AI assistants to understand how to generate valid configs.

**Parameters:** None

**Returns:** JSON with comprehensive schema documentation including:
- Full JSON Schema from Pydantic model
- Required vs optional fields
- Validation rules and scoring criteria
- Best practices and guidelines
- Complete example configuration
- Usage notes and workflow

#### get_config_template
Get a pre-configured config template for a specific domain. Templates include domain-appropriate instructions, example queries, and placeholders for customization.

**Parameters:**
- `domain` (string, optional): Type of analytics space (default: "minimal")
  - `minimal` - Bare minimum valid config (score ~70)
  - `sales` - Revenue tracking, transaction analysis, time-based metrics
  - `customer` - User behavior, segmentation, retention analysis
  - `inventory` - Stock levels, warehouse operations
  - `financial` - Budgets, expenses, P&L reporting
  - `hr` - Headcount, compensation, performance

**Returns:** JSON template with placeholders: `[CATALOG]`, `[SCHEMA]`, `[TABLE_NAME]`

#### generate_space_config (Deprecated)
> **This tool is deprecated.** Use `get_config_schema()` and `get_config_template()` instead.

Generate a complete Genie space configuration from natural language requirements using an external LLM serving endpoint.

**Parameters:**
- `requirements` (string, required): Natural language description of desired Genie space
- `warehouse_id` (string, required): SQL warehouse ID for query execution
- `catalog_name` (string, required): Unity Catalog name to use
- `serving_endpoint_name` (string, optional): Serving endpoint name (uses default if not provided)
- `validate_sql` (bool, optional): Whether to validate SQL syntax (default: true)

**Returns:** JSON with generated configuration, reasoning, confidence score, and validation report

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
    config_json=json.dumps(config),
    title="Sales Analytics"
)
```

### Conversational Queries

**Ask a question:**
```python
result = await ask_genie(
    space_id="01ef...",
    question="What were the top 10 selling products last week?",
    timeout_seconds=300
)
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

**Ask Claude to create a Genie space:**
```
Create a Genie space for my sales data in main.sales.transactions
```

Behind the scenes, Claude will:
1. Call `get_config_schema()` to understand the format
2. Call `get_config_template(domain="sales")` to get a starting point
3. Generate a config by replacing placeholders with your table info
4. Call `validate_space_config()` to check quality
5. Call `create_genie_space()` to create the space

## Architecture

```
MCP Server (stdio)
├── Space Management Tools (CRUD via Databricks SDK)
├── Conversation Tools (async polling, rate limiting)
├── Config Generation Tools (schema-driven)
└── Skills (high-level workflow prompts)
    ├── /create-space  → Space Orchestrator + Warehouse Discovery
    ├── /ask           → Conversation Manager + Result Formatter
    ├── /inspect       → Config Analyzer
    └── /bulk          → Batch Operations
```

### Key Components

- **fastmcp** - Python MCP framework with decorator-based tools
- **Databricks SDK** - Official Python SDK for API access
- **Pydantic** - Data validation and settings management
- **sqlparse** - SQL syntax validation
- **asyncio** - Async polling for long-running queries

### Internal: Config Transformation

The server automatically transforms between two formats:
- **User-Facing:** `GenieSpaceConfig` (Pydantic model, developer-friendly)
- **API Format:** Protobuf JSON v2 (Databricks internal format)

The transformation happens transparently inside `create_genie_space` and `update_genie_space`. Users always work with the simpler `GenieSpaceConfig` format.

### Rate Limiting

Genie API limits: **5 queries per minute** (Public Preview)

The server automatically:
- Tracks requests in a sliding window
- Blocks when limit reached
- Waits until window slides

### Known Limitations

- **Bulk Update:** Builds modified configs but requires `warehouse_id` which may not be available. Workaround: export config, modify, then use `update_genie_space` directly.
- **Clone Operation:** Not yet implemented in `/bulk`. Use export + modify + create workflow instead.
- **Preview-Only Mode:** The `/ask` parameter exists but is not yet implemented.

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
databricks auth login
./configure.sh
```

**Profile shows (not configured):**
```bash
databricks auth login --profile YOUR_PROFILE_NAME
```

### "No space ID provided and no recent conversation found"

**Solution:** Provide `space_id` or `space_name` explicitly:
```python
ask(question="What is revenue?", space_id="abc123")
```

### "Validation score low"

**Solution:** Review recommendations and improve config:
```python
result = create_space(catalog_name="main", schema_name="sales", table_names="orders", expert=True)
# Add more instructions, examples, SQL snippets, then create manually
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
│   ├── skills/
│   │   ├── create_space_skill.py     # /create-space workflow
│   │   ├── ask_skill.py              # /ask workflow
│   │   ├── inspect_skill.py          # /inspect workflow
│   │   ├── bulk_skill.py             # /bulk workflow
│   │   └── utils/
│   │       ├── warehouse_discovery.py # Auto warehouse selection
│   │       ├── conversation_manager.py# Conversation state tracking
│   │       ├── result_formatter.py   # Adaptive result formatting
│   │       ├── space_orchestrator.py  # Multi-step creation workflows
│   │       └── config_analyzer.py    # Config quality analysis
│   ├── client/
│   │   ├── genie_client.py           # Databricks API wrapper
│   │   └── polling.py                # Async polling utilities
│   ├── generators/
│   │   ├── space_config_generator.py # LLM config generation
│   │   ├── validator.py              # Config validation
│   │   └── prompts.py                # LLM prompt templates
│   ├── models/
│   │   ├── space.py                  # Pydantic models
│   │   ├── protobuf_format.py        # Config <-> Protobuf transformer
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
