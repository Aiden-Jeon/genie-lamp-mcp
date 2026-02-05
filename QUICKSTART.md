# Quick Start Guide

Get started with the Genie MCP Server in 5 minutes.

## Prerequisites

- Python 3.10+
- Databricks workspace with Genie enabled
- SQL warehouse ID
- Personal Access Token or OAuth credentials

## Installation

```bash
# Clone/navigate to the repository
cd genie-mcp-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
```env
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
```

## Test the Server

Run a simple test to verify everything works:

```bash
# Check imports
python -c "from genie_mcp_server import config; print('✓ Config OK')"

# View example usage
python examples/basic_usage.py
```

## Use with Claude Desktop

1. Find your Claude Desktop config:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the MCP server:
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

3. Restart Claude Desktop

4. Verify tools are available - you should see 13 Genie tools in Claude

## First Steps

### 1. List Existing Spaces

In Claude Desktop, ask:
> "List all Genie spaces in my workspace"

Claude will use the `list_genie_spaces` tool.

### 2. Generate a Configuration

Ask Claude:
> "Generate a Genie space configuration for analyzing sales data. Use tables from main.sales schema: orders, customers, products"

Claude will use `extract_table_metadata` and `generate_space_config` tools.

### 3. Create a Space

Once you have a configuration:
> "Create a Genie space with this configuration using warehouse ID abc123"

Claude will use `create_genie_space` tool.

### 4. Ask Questions

After creating a space:
> "Ask the space 'What were the top 10 selling products last week?'"

Claude will use `ask_genie` tool, automatically handling polling and rate limiting.

## Common Commands

**List spaces:**
```
List all Genie spaces
```

**Get space details:**
```
Get details for space ID 01ef...
```

**Generate config:**
```
Generate a Genie space config for [your requirements]
```

**Create space:**
```
Create a Genie space with warehouse ID [id] using this config: [config]
```

**Ask questions:**
```
Ask space [space_id]: "What were total sales last month?"
```

**Validate config:**
```
Validate this Genie space configuration: [config]
```

## Troubleshooting

### "Authentication failed"
- Check `DATABRICKS_HOST` is correct (including https://)
- Verify `DATABRICKS_TOKEN` is valid
- Test with: `databricks workspace ls /` (using Databricks CLI)

### "Module not found"
- Ensure virtual environment is activated
- Re-run: `pip install -e .`

### "Rate limit exceeded"
- Genie allows 5 queries/minute
- Wait 60 seconds before trying again
- Tools automatically handle rate limiting

### "Timeout"
- Increase `timeout_seconds` for complex queries
- Default is 300 seconds (5 minutes)

## Next Steps

1. Read [TOOLS.md](TOOLS.md) for detailed tool documentation
2. Check [README.md](README.md) for architecture details
3. Explore [examples/](examples/) for more usage patterns
4. Review validation reports to improve configuration quality

## Support

- Documentation: [Databricks Genie Docs](https://docs.databricks.com/genie/)
- Issues: Create a GitHub issue
- Examples: See `examples/basic_usage.py`

## Tips

1. **Start with metadata extraction** - Use `extract_table_metadata` before generating configs
2. **Validate before deploying** - Always validate generated configs
3. **Test with simple questions** - Verify space works with basic queries first
4. **Iterate on instructions** - Refine based on validation warnings
5. **Monitor quality scores** - Aim for 80+ validation score

Happy building with Genie!
