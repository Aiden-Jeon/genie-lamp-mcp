"""Domain-specific configuration templates for Genie spaces."""

from typing import Literal

# Domain-specific templates with placeholders for customization
TEMPLATES = {
    "minimal": {
        "space_name": "Quick Start Space",
        "description": "A minimal Genie space for [CATALOG].[SCHEMA].[TABLE_NAME]",
        "purpose": "Enable natural language queries on your data",
        "tables": [
            {
                "catalog_name": "[CATALOG]",
                "schema_name": "[SCHEMA]",
                "table_name": "[TABLE_NAME]",
            }
        ],
        "instructions": [
            {
                "content": "## Time Filtering\nDefault to last 30 days when no time range specified.",
                "priority": 1,
            }
        ],
        "example_sql_queries": [
            {
                "question": "Show me recent records",
                "sql_query": "SELECT * FROM [CATALOG].[SCHEMA].[TABLE_NAME] LIMIT 100",
            }
        ],
    },
    "sales": {
        "space_name": "Sales Analytics",
        "description": "Natural language analytics for sales transactions and revenue data",
        "purpose": "Enable sales team to analyze revenue, transactions, and product performance",
        "tables": [
            {
                "catalog_name": "[CATALOG]",
                "schema_name": "[SCHEMA]",
                "table_name": "[TABLE_NAME]",
            }
        ],
        "instructions": [
            {
                "content": "## Date Filtering\nUse `transaction_date` or `order_date` for time-based filtering. Default to last 7 days when not specified.",
                "priority": 1,
            },
            {
                "content": "## Revenue Calculations\nAlways cast revenue calculations to DECIMAL(38,2) for precision:\n- Example: `CAST(SUM(amount) AS DECIMAL(38,2))`\n- Use `try_divide()` to avoid division by zero",
                "priority": 2,
            },
            {
                "content": "## Top Products\nWhen showing top products:\n- Use `LIMIT 10` by default\n- Order by sales or revenue DESC\n- Include product name and total",
                "priority": 3,
            },
            {
                "content": "## Time Periods\nSupport common time periods:\n- Last 7 days: `>= CURRENT_DATE - 7`\n- Last 30 days: `>= CURRENT_DATE - 30`\n- This month: `>= DATE_TRUNC('MONTH', CURRENT_DATE)`\n- Last month: Use `DATE_SUB()` function",
                "priority": 4,
            },
        ],
        "example_sql_queries": [
            {
                "question": "What were total sales last week?",
                "sql_query": "SELECT CAST(SUM(amount) AS DECIMAL(38,2)) as total_sales FROM [CATALOG].[SCHEMA].[TABLE_NAME] WHERE transaction_date >= CURRENT_DATE - 7",
            },
            {
                "question": "Top 10 products by revenue",
                "sql_query": "SELECT product_name, CAST(SUM(amount) AS DECIMAL(38,2)) as revenue FROM [CATALOG].[SCHEMA].[TABLE_NAME] GROUP BY product_name ORDER BY revenue DESC LIMIT 10",
            },
            {
                "question": "Daily sales trend for the last 30 days",
                "sql_query": "SELECT DATE(transaction_date) as sale_date, CAST(SUM(amount) AS DECIMAL(38,2)) as daily_sales FROM [CATALOG].[SCHEMA].[TABLE_NAME] WHERE transaction_date >= CURRENT_DATE - 30 GROUP BY DATE(transaction_date) ORDER BY sale_date",
            },
        ],
        "sql_snippets": {
            "measures": [
                {
                    "alias": "total_revenue",
                    "sql": "CAST(SUM(amount) AS DECIMAL(38,2))",
                    "display_name": "Total Revenue",
                    "synonyms": ["revenue", "sales", "total sales"],
                    "instruction": "Use for calculating total sales or revenue",
                }
            ]
        },
    },
    "customer": {
        "space_name": "Customer Analytics",
        "description": "Natural language analytics for customer behavior and segmentation",
        "purpose": "Enable customer insights team to analyze user behavior, retention, and segmentation",
        "tables": [
            {
                "catalog_name": "[CATALOG]",
                "schema_name": "[SCHEMA]",
                "table_name": "[TABLE_NAME]",
            }
        ],
        "instructions": [
            {
                "content": "## Customer Identification\nUse `customer_id` or `user_id` for unique customer identification.",
                "priority": 1,
            },
            {
                "content": "## Date Columns\nUse `signup_date` or `registration_date` for customer acquisition analysis.\nUse `last_activity_date` or `last_purchase_date` for engagement analysis.",
                "priority": 2,
            },
            {
                "content": "## Customer Counts\nAlways use `COUNT(DISTINCT customer_id)` when counting customers to avoid duplicates.",
                "priority": 3,
            },
            {
                "content": "## Segmentation\nCommon segments:\n- New customers: signed up in last 30 days\n- Active customers: activity in last 90 days\n- Churned customers: no activity in last 180 days",
                "priority": 4,
            },
        ],
        "example_sql_queries": [
            {
                "question": "How many new customers signed up last month?",
                "sql_query": "SELECT COUNT(DISTINCT customer_id) as new_customers FROM [CATALOG].[SCHEMA].[TABLE_NAME] WHERE signup_date >= DATE_TRUNC('MONTH', CURRENT_DATE - 30) AND signup_date < DATE_TRUNC('MONTH', CURRENT_DATE)",
            },
            {
                "question": "What is the customer retention rate?",
                "sql_query": "SELECT COUNT(DISTINCT CASE WHEN last_activity_date >= CURRENT_DATE - 90 THEN customer_id END) * 100.0 / COUNT(DISTINCT customer_id) as retention_rate FROM [CATALOG].[SCHEMA].[TABLE_NAME]",
            },
            {
                "question": "Top 10 customers by total purchases",
                "sql_query": "SELECT customer_id, COUNT(*) as purchase_count, CAST(SUM(purchase_amount) AS DECIMAL(38,2)) as total_spent FROM [CATALOG].[SCHEMA].[TABLE_NAME] GROUP BY customer_id ORDER BY total_spent DESC LIMIT 10",
            },
        ],
    },
    "inventory": {
        "space_name": "Inventory Management",
        "description": "Natural language analytics for inventory levels and warehouse operations",
        "purpose": "Enable operations team to track stock levels, warehouse capacity, and inventory movement",
        "tables": [
            {
                "catalog_name": "[CATALOG]",
                "schema_name": "[SCHEMA]",
                "table_name": "[TABLE_NAME]",
            }
        ],
        "instructions": [
            {
                "content": "## Stock Levels\nUse `quantity_on_hand` or `stock_level` for current inventory.\nUse `reorder_point` to identify items needing restocking.",
                "priority": 1,
            },
            {
                "content": "## Warehouse Identification\nUse `warehouse_id` or `location_id` to filter by specific warehouses.",
                "priority": 2,
            },
            {
                "content": "## Low Stock Alerts\nDefine low stock as: `quantity_on_hand < reorder_point`\nDefine out of stock as: `quantity_on_hand = 0`",
                "priority": 3,
            },
            {
                "content": "## Inventory Value\nCalculate inventory value as: `quantity_on_hand * unit_cost`\nCast to DECIMAL(38,2) for precision.",
                "priority": 4,
            },
        ],
        "example_sql_queries": [
            {
                "question": "Show me items with low stock",
                "sql_query": "SELECT product_id, product_name, quantity_on_hand, reorder_point FROM [CATALOG].[SCHEMA].[TABLE_NAME] WHERE quantity_on_hand < reorder_point ORDER BY quantity_on_hand",
            },
            {
                "question": "What is the total inventory value?",
                "sql_query": "SELECT CAST(SUM(quantity_on_hand * unit_cost) AS DECIMAL(38,2)) as total_value FROM [CATALOG].[SCHEMA].[TABLE_NAME]",
            },
            {
                "question": "Which warehouse has the most inventory?",
                "sql_query": "SELECT warehouse_id, SUM(quantity_on_hand) as total_units FROM [CATALOG].[SCHEMA].[TABLE_NAME] GROUP BY warehouse_id ORDER BY total_units DESC LIMIT 1",
            },
        ],
    },
    "financial": {
        "space_name": "Financial Analytics",
        "description": "Natural language analytics for budgets, expenses, and financial reporting",
        "purpose": "Enable finance team to analyze spending, budgets, and P&L statements",
        "tables": [
            {
                "catalog_name": "[CATALOG]",
                "schema_name": "[SCHEMA]",
                "table_name": "[TABLE_NAME]",
            }
        ],
        "instructions": [
            {
                "content": "## Amount Calculations\nAlways cast financial amounts to DECIMAL(38,2) for precision.\nUse `try_divide()` for percentage calculations to avoid division by zero.",
                "priority": 1,
            },
            {
                "content": "## Date Columns\nUse `transaction_date` or `posting_date` for financial periods.\nDefault to current fiscal year when no period is specified.",
                "priority": 2,
            },
            {
                "content": "## Account Types\nRevenue accounts: typically positive amounts\nExpense accounts: typically positive amounts (not negative)\nUse `account_type` or `account_category` for classification.",
                "priority": 3,
            },
            {
                "content": "## Budget Variance\nCalculate variance as: `actual - budget`\nCalculate variance percentage as: `try_divide((actual - budget), budget) * 100`",
                "priority": 4,
            },
        ],
        "example_sql_queries": [
            {
                "question": "What were total expenses last quarter?",
                "sql_query": "SELECT CAST(SUM(amount) AS DECIMAL(38,2)) as total_expenses FROM [CATALOG].[SCHEMA].[TABLE_NAME] WHERE account_type = 'Expense' AND transaction_date >= DATE_TRUNC('QUARTER', CURRENT_DATE - 90) AND transaction_date < DATE_TRUNC('QUARTER', CURRENT_DATE)",
            },
            {
                "question": "Show budget vs actual by department",
                "sql_query": "SELECT department, CAST(SUM(budget_amount) AS DECIMAL(38,2)) as budget, CAST(SUM(actual_amount) AS DECIMAL(38,2)) as actual, CAST(SUM(actual_amount - budget_amount) AS DECIMAL(38,2)) as variance FROM [CATALOG].[SCHEMA].[TABLE_NAME] GROUP BY department ORDER BY variance DESC",
            },
            {
                "question": "Top 5 expense categories",
                "sql_query": "SELECT category, CAST(SUM(amount) AS DECIMAL(38,2)) as total_expense FROM [CATALOG].[SCHEMA].[TABLE_NAME] WHERE account_type = 'Expense' GROUP BY category ORDER BY total_expense DESC LIMIT 5",
            },
        ],
    },
    "hr": {
        "space_name": "HR Analytics",
        "description": "Natural language analytics for headcount, compensation, and performance",
        "purpose": "Enable HR team to analyze employee data, compensation, and organizational metrics",
        "tables": [
            {
                "catalog_name": "[CATALOG]",
                "schema_name": "[SCHEMA]",
                "table_name": "[TABLE_NAME]",
            }
        ],
        "instructions": [
            {
                "content": "## Employee Identification\nUse `employee_id` for unique employee identification.\nUse `is_active` or `employment_status = 'Active'` to filter current employees.",
                "priority": 1,
            },
            {
                "content": "## Date Columns\nUse `hire_date` for tenure calculations.\nUse `termination_date` for turnover analysis.\nUse `last_review_date` for performance tracking.",
                "priority": 2,
            },
            {
                "content": "## Compensation Calculations\nAlways cast salary amounts to DECIMAL(38,2).\nCalculate averages using AVG() function.\nConsider using COUNT(DISTINCT employee_id) for headcount.",
                "priority": 3,
            },
            {
                "content": "## Tenure Calculation\nCalculate years of service as: `DATEDIFF(CURRENT_DATE, hire_date) / 365.25`\nRound to appropriate decimal places for reporting.",
                "priority": 4,
            },
        ],
        "example_sql_queries": [
            {
                "question": "What is the current headcount by department?",
                "sql_query": "SELECT department, COUNT(DISTINCT employee_id) as headcount FROM [CATALOG].[SCHEMA].[TABLE_NAME] WHERE is_active = true GROUP BY department ORDER BY headcount DESC",
            },
            {
                "question": "What is the average salary by department?",
                "sql_query": "SELECT department, CAST(AVG(salary) AS DECIMAL(38,2)) as avg_salary FROM [CATALOG].[SCHEMA].[TABLE_NAME] WHERE is_active = true GROUP BY department ORDER BY avg_salary DESC",
            },
            {
                "question": "How many employees were hired in the last 6 months?",
                "sql_query": "SELECT COUNT(DISTINCT employee_id) as new_hires FROM [CATALOG].[SCHEMA].[TABLE_NAME] WHERE hire_date >= CURRENT_DATE - 180",
            },
        ],
    },
}


def get_template(
    domain: Literal["minimal", "sales", "customer", "inventory", "financial", "hr"] = "minimal",
) -> dict:
    """Get configuration template for specified domain.

    Args:
        domain: Type of analytics space (minimal/sales/customer/inventory/financial/hr)

    Returns:
        Template configuration with domain-appropriate metadata, instructions,
        and example queries. Contains placeholders:
        - [CATALOG]: Replace with your Unity Catalog name
        - [SCHEMA]: Replace with your schema name
        - [TABLE_NAME]: Replace with your table name

    Usage:
        1. Get template for your domain
        2. Replace [CATALOG], [SCHEMA], [TABLE_NAME] with actual values
        3. Customize instructions and examples based on actual column names
        4. Validate with validate_space_config() tool
        5. Create space with create_genie_space() tool
    """
    return TEMPLATES.get(domain, TEMPLATES["minimal"])
