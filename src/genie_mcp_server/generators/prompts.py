"""LLM prompt templates for Genie space configuration generation."""

BEST_PRACTICES = """
## Best Practices for Genie Space Configuration

### Instructions (DO)
- Be specific: Reference exact column names using backticks (e.g., `event_date`, `user_id`)
- Use markdown formatting: headers (##), bullet lists (-), bold (**important**)
- Provide context: Explain when and how to use specific patterns
- Include examples: Show concrete SQL patterns or values
- Set priorities: Critical instructions should have priority=1

### Instructions (DON'T)
- Avoid vague terms: "appropriate", "relevant", "as needed"
- Don't be generic: "Handle dates properly" → "Use `event_date` for filtering by date"
- Don't skip formatting: Plain text is harder to parse

### SQL Best Practices
- Use explicit JOINs with ON clauses (not comma-separated tables)
- Use date functions: CURRENT_DATE, DATE_SUB(), DATE_TRUNC()
- Add LIMIT clauses to prevent large result sets
- Cast aggregates to DECIMAL(38,2) for precision
- Use try_divide() to avoid division by zero

### SQL Expressions
- Filters: WHERE conditions (e.g., `table.price > 100`)
- Expressions: Dimensions/calculated fields (e.g., `YEAR(orders.order_date)`)
- Measures: Aggregations (e.g., `SUM(orders.amount)`)

### Example SQL Queries
- Provide at least 3-5 realistic examples
- Cover different query types: aggregation, filtering, joins
- Use actual table/column names from the configuration
"""

OUTPUT_FORMAT = """
## Output Format

You must output valid JSON matching this schema:

```json
{
  "genie_space_config": {
    "space_name": "Descriptive Name",
    "description": "What this space is for",
    "purpose": "Target audience and use cases",
    "tables": [
      {
        "catalog_name": "catalog_name",
        "schema_name": "schema_name",
        "table_name": "table_name",
        "description": "Optional table description"
      }
    ],
    "join_specifications": [
      {
        "left_table": "catalog.schema.table1",
        "right_table": "catalog.schema.table2",
        "join_type": "INNER",
        "join_condition": "table1.id = table2.foreign_id",
        "description": "Relationship explanation",
        "instruction": "When to use this join"
      }
    ],
    "instructions": [
      {
        "content": "## Specific instruction\\n- Use `column_name` for X\\n- Filter by Y when Z",
        "priority": 1
      }
    ],
    "example_sql_queries": [
      {
        "question": "Natural language question",
        "sql_query": "Complete SQL query",
        "description": "What this query demonstrates"
      }
    ],
    "sql_snippets": {
      "filters": [
        {
          "sql": "table.price > 100",
          "display_name": "High Price Items",
          "synonyms": ["expensive", "premium"]
        }
      ],
      "expressions": [
        {
          "alias": "order_year",
          "sql": "YEAR(orders.order_date)",
          "display_name": "Order Year",
          "synonyms": ["year"],
          "instruction": "Use for yearly aggregation"
        }
      ],
      "measures": [
        {
          "alias": "total_revenue",
          "sql": "SUM(orders.amount)",
          "display_name": "Total Revenue",
          "synonyms": ["revenue", "sales"],
          "instruction": "Use for revenue calculations"
        }
      ]
    },
    "benchmark_questions": [
      {
        "question": "Test question for validation"
      }
    ],
    "warehouse_id": "warehouse_id_here",
    "enable_data_sampling": true
  },
  "reasoning": "Explanation of design choices",
  "confidence_score": 0.95
}
```
"""


def build_config_generation_prompt(
    requirements: str,
    catalog_name: str,
    warehouse_id: str,
    table_metadata: str | None = None,
) -> str:
    """Build prompt for generating Genie space configuration.

    Args:
        requirements: User's natural language requirements
        catalog_name: Unity Catalog name
        warehouse_id: SQL warehouse ID
        table_metadata: Optional table metadata context

    Returns:
        Formatted prompt string
    """
    table_context = ""
    if table_metadata:
        table_context = f"""
## Available Table Metadata

{table_metadata}

Use this metadata to understand table structures, columns, and relationships.
"""

    prompt = f"""You are an expert in creating Databricks Genie spaces. Generate a complete, high-quality Genie space configuration based on the user's requirements.

{BEST_PRACTICES}

{OUTPUT_FORMAT}

{table_context}

## Configuration Parameters

- Catalog: {catalog_name}
- Warehouse ID: {warehouse_id}

## User Requirements

{requirements}

## Task

Generate a complete Genie space configuration that:
1. Addresses all user requirements
2. Follows best practices for instructions, SQL, and structure
3. Includes at least 3-5 example SQL queries
4. Uses specific column/table names (backticks in instructions)
5. Provides clear, actionable guidance

Respond ONLY with valid JSON matching the schema above.
"""

    return prompt


def build_table_metadata_prompt(
    catalog_name: str, schema_name: str, table_names: list[str] | None = None
) -> str:
    """Build prompt for extracting table metadata context.

    Args:
        catalog_name: Catalog name
        schema_name: Schema name
        table_names: Optional list of specific tables to include

    Returns:
        Formatted context string for table metadata
    """
    table_filter = ""
    if table_names:
        table_list = "', '".join(table_names)
        table_filter = f"Tables: {table_list}"

    return f"""Catalog: {catalog_name}
Schema: {schema_name}
{table_filter}

Extract table metadata including:
- Table names and descriptions
- Column names and data types
- Primary/foreign key relationships
"""
