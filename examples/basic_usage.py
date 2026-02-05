"""Basic usage examples for Genie MCP Server tools.

This script demonstrates how to use the Genie MCP Server tools programmatically.
Note: These examples assume the MCP server is running and configured.
"""

import asyncio
import json


async def example_space_management():
    """Example: Create and manage a Genie space."""
    print("=== Space Management Example ===\n")

    # Example configuration
    config = {
        "space_name": "Sales Analytics",
        "description": "Natural language querying for sales data",
        "purpose": "Enable business users to analyze sales trends and performance",
        "tables": [
            {
                "catalog_name": "main",
                "schema_name": "sales",
                "table_name": "transactions",
                "description": "Daily sales transactions",
            }
        ],
        "instructions": [
            {
                "content": "## Date Filtering\n- Use `transaction_date` for filtering by date\n- Default to last 7 days when no date range specified",
                "priority": 1,
            }
        ],
        "example_sql_queries": [
            {
                "question": "What were the top 10 selling products last week?",
                "sql_query": "SELECT product_name, COUNT(*) as sales FROM transactions WHERE transaction_date >= CURRENT_DATE - 7 GROUP BY product_name ORDER BY sales DESC LIMIT 10",
            }
        ],
        "warehouse_id": "your-warehouse-id",
    }

    print(f"Configuration to create:\n{json.dumps(config, indent=2)}\n")

    # In practice, you would call the MCP tool:
    # result = create_genie_space(
    #     warehouse_id="your-warehouse-id",
    #     serialized_space=json.dumps(config),
    #     title="Sales Analytics"
    # )
    # print(f"Created space: {result}")


async def example_querying():
    """Example: Ask questions to Genie."""
    print("\n=== Querying Example ===\n")

    space_id = "your-space-id"
    question = "What were the top 10 selling products last week?"

    print(f"Space ID: {space_id}")
    print(f"Question: {question}\n")

    # In practice, you would call the MCP tool:
    # result = await ask_genie(
    #     space_id=space_id,
    #     question=question,
    #     timeout_seconds=300
    # )
    # result_dict = json.loads(result)
    # print(f"Response: {result_dict['response_text']}")
    # print(f"SQL Query: {result_dict['sql_query']}")
    # print(f"Results: {result_dict['query_result']}")


async def example_config_generation():
    """Example: Generate configuration from requirements."""
    print("\n=== Configuration Generation Example ===\n")

    requirements = """
    Create a Genie space for analyzing customer orders in an e-commerce platform.

    Requirements:
    - Track order trends over time (daily, weekly, monthly)
    - Analyze customer segments and behavior
    - Monitor revenue and product performance
    - Identify top customers and products

    Tables available:
    - main.sales.orders (order_id, customer_id, order_date, total_amount)
    - main.sales.customers (customer_id, customer_name, segment)
    - main.sales.order_items (order_id, product_id, quantity, price)
    - main.sales.products (product_id, product_name, category)

    Key metrics to track:
    - Total revenue
    - Average order value
    - Customer lifetime value
    - Product conversion rate
    """

    print(f"Requirements:\n{requirements}\n")

    # In practice, you would call the MCP tool:
    # result = generate_space_config(
    #     requirements=requirements,
    #     warehouse_id="your-warehouse-id",
    #     catalog_name="main",
    #     validate_sql=True
    # )
    # result_dict = json.loads(result)
    # print(f"Generated configuration:\n{json.dumps(result_dict['genie_space_config'], indent=2)}")
    # print(f"\nReasoning: {result_dict['reasoning']}")
    # print(f"Confidence Score: {result_dict['confidence_score']}")
    # print(f"Validation Score: {result_dict['validation_report']['score']}/100")


async def example_table_metadata():
    """Example: Extract table metadata for context."""
    print("\n=== Table Metadata Extraction Example ===\n")

    catalog_name = "main"
    schema_name = "sales"
    table_names = ["orders", "customers", "products"]

    print(f"Catalog: {catalog_name}")
    print(f"Schema: {schema_name}")
    print(f"Tables: {', '.join(table_names)}\n")

    # In practice, you would call the MCP tool:
    # result = extract_table_metadata(
    #     catalog_name=catalog_name,
    #     schema_name=schema_name,
    #     table_names=table_names
    # )
    # metadata = json.loads(result)
    # print(f"Extracted metadata for {len(metadata['tables'])} tables")
    # for table in metadata['tables']:
    #     print(f"\nTable: {table['table_name']}")
    #     print(f"  Columns: {len(table['columns'])}")
    #     print(f"  Type: {table['table_type']}")


async def main():
    """Run all examples."""
    print("Genie MCP Server - Usage Examples")
    print("=" * 50)

    await example_space_management()
    await example_querying()
    await example_config_generation()
    await example_table_metadata()

    print("\n" + "=" * 50)
    print("Note: These are example templates. Uncomment the MCP tool calls")
    print("and provide actual credentials to run against a real Databricks workspace.")


if __name__ == "__main__":
    asyncio.run(main())
