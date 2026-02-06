# Genie MCP Skills User Guide

This guide demonstrates how to use the 4 conversational skills for simplified Genie space management.

## Quick Start

The Genie MCP server now provides 4 high-level skills that simplify common workflows:

1. **`/create-space`** - Create spaces with guided setup
2. **`/ask`** - Ask questions with automatic conversation tracking
3. **`/inspect`** - Analyze space health and export configs
4. **`/bulk`** - Batch operations on multiple spaces

## Skill 1: `/create-space` - Space Creation Wizard

### Basic Usage

Create a space with automatic warehouse discovery:

```python
create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders,customers,products"
)
```

### Quick Mode

Skip validation and create immediately:

```python
create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders",
    domain="sales",
    quick=True
)
```

### Expert Mode

Get the configuration JSON for manual editing:

```python
create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders",
    expert=True
)
```

### With Custom Settings

```python
create_space(
    catalog_name="main",
    schema_name="finance",
    table_names="transactions,accounts,invoices",
    warehouse_id="581ed75401284b97",  # Specific warehouse
    domain="financial",                # Domain template
    space_name="Q4 Financial Analytics"  # Custom name
)
```

### Available Domains

- `minimal` - Basic setup (default)
- `sales` - Sales analytics optimized
- `customer` - Customer data focused
- `inventory` - Inventory management
- `financial` - Financial analysis
- `hr` - Human resources

## Skill 2: `/ask` - Q&A Assistant

### Basic Usage

Ask a question to a specific space:

```python
ask(
    question="What is the total revenue for last month?",
    space_id="01234567-89ab-cdef-0123-456789abcdef"
)
```

### By Space Name

Use space name instead of ID:

```python
ask(
    question="Show top 10 customers by revenue",
    space_name="Sales Analytics"
)
```

### Follow-up Questions

The skill automatically continues conversations:

```python
# First question (starts new conversation)
ask(question="What is total revenue?", space_id="abc123")

# Follow-up (continues same conversation automatically)
ask(question="Show breakdown by product category")

# Another follow-up (still same conversation)
ask(question="Filter to last quarter only")
```

### Start New Conversation

Force a new conversation instead of continuing:

```python
ask(
    question="Different topic: show inventory levels",
    space_id="abc123",
    new_conversation=True
)
```

### Verbose Mode

Show all rows (not just top 10):

```python
ask(
    question="List all products",
    space_id="abc123",
    verbose=True
)
```

### Custom Timeout

For complex queries that take longer:

```python
ask(
    question="Complex aggregation across millions of rows",
    space_id="abc123",
    timeout=600  # 10 minutes
)
```

## Skill 3: `/inspect` - Space Inspector

### Health Check

Analyze space configuration and activity:

```python
inspect(
    space_id="abc123",
    mode="health"
)
```

**Output includes:**
- Overall health score (0-100)
- Configuration metrics (tables, instructions, examples)
- Activity metrics (conversation count, last activity)
- Actionable recommendations

### Export Configuration

Extract space configuration as JSON:

```python
inspect(
    space_id="abc123",
    mode="export"
)
```

Save to file:

```python
inspect(
    space_id="abc123",
    mode="export",
    output_file="my_space_config.json"
)
```

### Compare Spaces

See differences between two spaces:

```python
inspect(
    space_id="abc123",
    mode="diff",
    compare_with="def456"
)
```

**Output includes:**
- Side-by-side metric comparison
- Tables only in Space 1
- Tables only in Space 2
- Configuration differences

### Find Spaces

Search for spaces by table or keyword:

```python
# Find spaces containing specific tables
inspect(
    space_id="",  # Required but unused for find mode
    mode="find",
    search_tables="orders,customers"
)

# Find spaces by keyword
inspect(
    space_id="",
    mode="find",
    search_keywords="sales,revenue"
)

# Combine both
inspect(
    space_id="",
    mode="find",
    search_tables="transactions",
    search_keywords="financial"
)
```

## Skill 4: `/bulk` - Bulk Operations

### Update Multiple Spaces

Add instructions to multiple spaces:

```python
# Dry run first (preview changes)
bulk(
    operation="update",
    space_ids="abc123,def456,ghi789",
    add_instructions="Always use fiscal year dates\nPrefer aggregated metrics",
    dry_run=True
)

# Apply changes
bulk(
    operation="update",
    space_ids="abc123,def456,ghi789",
    add_instructions="Always use fiscal year dates\nPrefer aggregated metrics",
    dry_run=False
)
```

Add tables to multiple spaces:

```python
bulk(
    operation="update",
    space_ids="abc123,def456",
    add_tables="main.sales.returns,main.sales.refunds",
    dry_run=True
)
```

### Delete Multiple Spaces

By explicit IDs:

```python
# Dry run first (preview deletions)
bulk(
    operation="delete",
    space_ids="test1,test2,test3",
    dry_run=True
)

# Actually delete
bulk(
    operation="delete",
    space_ids="test1,test2,test3",
    dry_run=False
)
```

By pattern matching:

```python
# Delete all spaces starting with "test-"
bulk(
    operation="delete",
    pattern="test-*",
    dry_run=True
)

# Delete all spaces ending with "-dev"
bulk(
    operation="delete",
    pattern="*-dev",
    dry_run=True
)

# Delete all spaces with "staging" anywhere in name
bulk(
    operation="delete",
    pattern="*staging*",
    dry_run=True
)
```

**⚠️ Important:** Always use `dry_run=True` first to preview deletions!

## Common Workflows

### Workflow 1: Create and Validate a Space

```python
# 1. Create space with guided mode
result = create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders,customers",
    domain="sales"
)

# Extract space_id from result
space_id = "..."  # From result output

# 2. Check health
inspect(space_id=space_id, mode="health")

# 3. Test with questions
ask(question="What tables are available?", space_id=space_id)
ask(question="Show sample data from orders")
```

### Workflow 2: Clone and Modify a Space

```python
# 1. Export existing space config
inspect(
    space_id="original-space-id",
    mode="export",
    output_file="original_config.json"
)

# 2. Edit the config file manually
# (change tables, instructions, etc.)

# 3. Create new space with modified config
# (Use create_genie_space tool with edited config)
```

### Workflow 3: Batch Space Management

```python
# 1. Find all spaces using a specific table
inspect(
    space_id="",
    mode="find",
    search_tables="main.sales.transactions"
)

# 2. Add common instruction to all found spaces
bulk(
    operation="update",
    space_ids="space1,space2,space3",  # From find results
    add_instructions="Always filter to last 365 days by default",
    dry_run=True
)

# 3. Verify changes
for space_id in ["space1", "space2", "space3"]:
    inspect(space_id=space_id, mode="health")
```

### Workflow 4: Conversational Q&A Session

```python
# Natural conversation flow - the skill tracks context
ask(question="Show me revenue trends", space_name="Sales Analytics")
# → Skill: Started new conversation

ask(question="Break it down by region")
# → Skill: Continuing conversation (reuses conversation_id)

ask(question="Now show top 5 products in each region")
# → Skill: Still same conversation

ask(question="Export this to a dashboard")
# → Skill: Same conversation, 30min TTL maintained
```

## Tips and Best Practices

### 1. Use Quick Mode for Development

```python
# Fast iteration during development
create_space(
    catalog_name="main",
    schema_name="test",
    table_names="sample_data",
    quick=True  # Skips validation
)
```

### 2. Use Expert Mode for Complex Configs

```python
# Get the config, edit it, then create manually
result = create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders",
    expert=True  # Returns JSON config
)

# Edit the config, then use create_genie_space tool directly
```

### 3. Always Dry-Run Bulk Deletes

```python
# ALWAYS preview first
bulk(operation="delete", pattern="test-*", dry_run=True)

# Review the output carefully

# Only then delete for real
bulk(operation="delete", pattern="test-*", dry_run=False)
```

### 4. Use Health Checks Regularly

```python
# Check space health after creation
inspect(space_id="abc123", mode="health")

# Act on recommendations
# Example: "Add more SQL measures" → Update config
```

### 5. Leverage Conversation Continuity

```python
# No need to track conversation_id manually
ask(question="First question", space_id="abc123")
ask(question="Follow-up")  # Automatically continues
ask(question="Another follow-up")  # Still same conversation

# Start fresh when needed
ask(question="New topic", space_id="abc123", new_conversation=True)
```

## Error Handling

### Rate Limiting

The `/ask` skill handles rate limits automatically:

```
⏳ Rate Limit Reached

You've reached the limit of 5 queries per minute. Waiting 15 seconds...
```

### Timeouts

Customize timeout for long-running queries:

```python
ask(
    question="Complex aggregation",
    space_id="abc123",
    timeout=600  # 10 minutes instead of default 5
)
```

### Warehouse Not Found

The skill auto-discovers warehouses, but you can override:

```python
create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders",
    warehouse_id="your-warehouse-id"  # Explicit warehouse
)
```

## Troubleshooting

### "No space ID provided and no recent conversation found"

**Solution:** Provide `space_id` or `space_name` explicitly:
```python
ask(question="What is revenue?", space_id="abc123")
```

### "Warehouse ID not found"

**Solution:** Check available warehouses or let the skill auto-discover:
```python
# Auto-discover (default behavior)
create_space(catalog_name="main", schema_name="sales", table_names="orders")

# Or specify explicitly
create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders",
    warehouse_id="581ed75401284b97"
)
```

### "Validation score low"

**Solution:** Review recommendations and improve config:
```python
# Check what's missing
result = create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders",
    expert=True  # Get full config
)

# Add more instructions, examples, SQL snippets
# Then create manually with create_genie_space tool
```

## Advanced Usage

### Programmatic Space Creation Pipeline

```python
# 1. Extract table metadata
metadata = extract_table_metadata(
    catalog_name="main",
    schema_name="sales"
)

# 2. Get domain template
template = get_config_template(domain="sales")

# 3. Create space
result = create_space(
    catalog_name="main",
    schema_name="sales",
    table_names="orders,customers",
    domain="sales",
    quick=True
)

# 4. Validate
space_id = extract_space_id(result)
health = inspect(space_id=space_id, mode="health")

# 5. Test
test_result = ask(
    question="Show sample data",
    space_id=space_id
)
```

### Multi-Space Comparison

```python
# Compare multiple spaces pairwise
spaces = ["space1", "space2", "space3"]

for i in range(len(spaces)):
    for j in range(i + 1, len(spaces)):
        print(f"Comparing {spaces[i]} vs {spaces[j]}")
        inspect(
            space_id=spaces[i],
            mode="diff",
            compare_with=spaces[j]
        )
```

## Next Steps

- See [SKILLS_IMPLEMENTATION.md](../SKILLS_IMPLEMENTATION.md) for technical details
- Check the main [README.md](../README.md) for installation and setup
- Review [examples/](../examples/) directory for more use cases

## Support

For issues or questions:
1. Check error messages and troubleshooting section above
2. Review the [SKILLS_IMPLEMENTATION.md](../SKILLS_IMPLEMENTATION.md) for known limitations
3. Open an issue on the GitHub repository
