"""Orchestrate multi-step space creation workflows."""

from typing import Optional
import json


class SpaceOrchestrator:
    """Orchestrates multi-step Genie space operations."""

    def generate_config_from_template(
        self,
        domain: str,
        catalog_name: str,
        schema_name: str,
        table_names: list[str],
        space_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """Generate config from domain template with table substitution.

        Args:
            domain: Domain template to use (minimal, sales, etc.).
            catalog_name: Unity Catalog name.
            schema_name: Schema name.
            table_names: List of table names.
            space_name: Optional space name (generated if not provided).
            description: Optional space description.

        Returns:
            GenieSpaceConfig dict ready for validation.
        """
        # Import here to avoid circular dependencies
        from genie_mcp_server.generators.templates import get_template

        # Get template
        template = get_template(domain)

        # Generate space name if not provided
        if not space_name:
            space_name = f"{domain.title()} Space - {schema_name}"

        # Update basic info
        config = template.copy()
        config["space_name"] = space_name
        if description:
            config["description"] = description

        # Update tables
        config["tables"] = [
            {
                "catalog_name": catalog_name,
                "schema_name": schema_name,
                "table_name": table_name
            }
            for table_name in table_names
        ]

        # Replace placeholders in instructions
        if "instructions" in config:
            config["instructions"] = [
                self._replace_placeholders(
                    instruction,
                    catalog_name,
                    schema_name,
                    table_names[0] if table_names else "table"
                )
                for instruction in config["instructions"]
            ]

        # Replace placeholders in example queries
        if "example_sql_queries" in config:
            config["example_sql_queries"] = [
                {
                    "question": example["question"],
                    "sql": self._replace_placeholders(
                        example["sql"],
                        catalog_name,
                        schema_name,
                        table_names[0] if table_names else "table"
                    )
                }
                for example in config["example_sql_queries"]
            ]

        # Replace placeholders in SQL snippets
        if "sql_snippets" in config:
            for snippet_type in ["measures", "expressions", "filters"]:
                if snippet_type in config["sql_snippets"]:
                    config["sql_snippets"][snippet_type] = [
                        {
                            **snippet,
                            "sql": self._replace_placeholders(
                                snippet["sql"],
                                catalog_name,
                                schema_name,
                                table_names[0] if table_names else "table"
                            )
                        }
                        for snippet in config["sql_snippets"][snippet_type]
                    ]

        return config

    def _replace_placeholders(
        self,
        text: str,
        catalog_name: str,
        schema_name: str,
        table_name: str
    ) -> str:
        """Replace placeholders in template text.

        Args:
            text: Text with placeholders.
            catalog_name: Catalog name to substitute.
            schema_name: Schema name to substitute.
            table_name: Table name to substitute.

        Returns:
            Text with placeholders replaced.
        """
        replacements = {
            "[CATALOG]": catalog_name,
            "[SCHEMA]": schema_name,
            "[TABLE_NAME]": table_name,
            "[TABLE]": f"{catalog_name}.{schema_name}.{table_name}",
        }

        result = text
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)

        return result

    def validate_and_score(
        self,
        config: dict,
        validate_sql: bool = True
    ) -> dict:
        """Validate config and calculate quality score.

        Args:
            config: GenieSpaceConfig dict.
            validate_sql: Whether to validate SQL syntax.

        Returns:
            Dict with validation result:
            {
                "valid": bool,
                "score": int (0-100),
                "errors": list[str],
                "warnings": list[str],
                "recommendations": list[str]
            }
        """
        # Import here to avoid circular dependencies
        from genie_mcp_server.generators.validator import ConfigValidator

        validator = ConfigValidator()
        validation = validator.validate(config, validate_sql=validate_sql)

        # Calculate quality score
        score = self._calculate_quality_score(config, validation)

        # Generate recommendations
        recommendations = self._generate_recommendations(config, validation)

        return {
            "valid": validation["valid"],
            "score": score,
            "errors": validation.get("errors", []),
            "warnings": validation.get("warnings", []),
            "recommendations": recommendations
        }

    def _calculate_quality_score(
        self,
        config: dict,
        validation: dict
    ) -> int:
        """Calculate quality score (0-100) for a config.

        Args:
            config: GenieSpaceConfig dict.
            validation: Validation result.

        Returns:
            Quality score (0-100).
        """
        score = 100

        # Major deductions
        if not validation["valid"]:
            score -= 40

        # Table checks
        table_count = len(config.get("tables", []))
        if table_count == 0:
            score -= 30
        elif table_count > 10:
            score -= 5  # Too many tables can be confusing

        # Instruction checks
        instruction_count = len(config.get("instructions", []))
        if instruction_count < 3:
            score -= 15
        elif instruction_count < 5:
            score -= 5

        # Example query checks
        example_count = len(config.get("example_sql_queries", []))
        if example_count < 3:
            score -= 10
        elif example_count < 5:
            score -= 5

        # SQL snippet checks
        snippets = config.get("sql_snippets", {})
        has_measures = len(snippets.get("measures", [])) > 0
        has_expressions = len(snippets.get("expressions", [])) > 0
        if not has_measures and not has_expressions:
            score -= 10

        # Join checks (if multiple tables)
        if table_count > 1:
            join_count = len(config.get("join_specifications", []))
            if join_count == 0:
                score -= 10
            elif join_count < table_count - 1:
                score -= 5

        return max(0, min(100, score))

    def _generate_recommendations(
        self,
        config: dict,
        validation: dict
    ) -> list[str]:
        """Generate actionable recommendations for config improvement.

        Args:
            config: GenieSpaceConfig dict.
            validation: Validation result.

        Returns:
            List of recommendation strings.
        """
        recommendations = []

        # Table recommendations
        table_count = len(config.get("tables", []))
        if table_count == 0:
            recommendations.append("Add at least one table to the space")
        elif table_count > 10:
            recommendations.append("Consider splitting into multiple spaces (10+ tables can be confusing)")

        # Instruction recommendations
        instruction_count = len(config.get("instructions", []))
        if instruction_count < 5:
            recommendations.append(
                f"Add more instructions to guide Genie (current: {instruction_count}, recommend: 5+)"
            )

        # Example recommendations
        example_count = len(config.get("example_sql_queries", []))
        if example_count < 5:
            recommendations.append(
                f"Add more example queries (current: {example_count}, recommend: 5+)"
            )

        # SQL snippet recommendations
        snippets = config.get("sql_snippets", {})
        measure_count = len(snippets.get("measures", []))
        expression_count = len(snippets.get("expressions", []))

        if measure_count == 0:
            recommendations.append("Add SQL measures for common metrics (e.g., revenue, count, average)")
        if expression_count == 0:
            recommendations.append("Add SQL expressions for common dimensions (e.g., date parts, categories)")

        # Join recommendations
        if table_count > 1:
            join_count = len(config.get("join_specifications", []))
            if join_count == 0:
                recommendations.append("Define join specifications to connect tables")
            elif join_count < table_count - 1:
                recommendations.append("Add more joins to fully connect all tables")

        return recommendations
