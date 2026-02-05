"""Configuration validation for Genie space configurations."""

import json
import re
import sqlparse
from typing import Any

from genie_mcp_server.models.space import GenieSpaceConfig, GenieSpaceTable, ValidationReport


class ConfigValidator:
    """Validates Genie space configurations for quality and correctness."""

    SQL_KEYWORDS = {
        "SELECT",
        "FROM",
        "WHERE",
        "JOIN",
        "GROUP",
        "BY",
        "ORDER",
        "LIMIT",
        "COUNT",
        "SUM",
        "AVG",
        "MIN",
        "MAX",
    }

    def __init__(self):
        """Initialize the validator."""
        pass

    def validate_config(
        self, config_dict: dict[str, Any], validate_sql: bool = True
    ) -> ValidationReport:
        """Validate a complete Genie space configuration.

        Args:
            config_dict: Configuration dictionary to validate
            validate_sql: Whether to perform SQL validation

        Returns:
            ValidationReport with validation results
        """
        errors = []
        warnings = []
        score = 100

        # 1. Schema validation with Pydantic
        try:
            config = GenieSpaceConfig(**config_dict)
        except Exception as e:
            errors.append(f"Schema validation failed: {str(e)}")
            return ValidationReport(valid=False, errors=errors, warnings=warnings, score=0)

        # 2. Check completeness
        completeness_errors, completeness_warnings, completeness_score = self._check_completeness(
            config
        )
        errors.extend(completeness_errors)
        warnings.extend(completeness_warnings)
        score = min(score, completeness_score)

        # 3. SQL validation
        if validate_sql:
            sql_errors, sql_warnings, sql_score = self._validate_sql(config)
            errors.extend(sql_errors)
            warnings.extend(sql_warnings)
            score = min(score, sql_score)

        # 4. Instruction quality check
        instr_warnings, instr_score = self._check_instruction_quality(config)
        warnings.extend(instr_warnings)
        score = min(score, instr_score)

        valid = len(errors) == 0
        return ValidationReport(valid=valid, errors=errors, warnings=warnings, score=score)

    def _check_completeness(
        self, config: GenieSpaceConfig
    ) -> tuple[list[str], list[str], int]:
        """Check configuration completeness.

        Returns:
            Tuple of (errors, warnings, score)
        """
        errors = []
        warnings = []
        score = 100

        # Must have at least one table
        if not config.tables:
            errors.append("No tables specified in configuration")
            score -= 40

        # Should have instructions
        if not config.instructions:
            warnings.append("No instructions provided - consider adding guidance")
            score -= 10

        # Should have example queries
        if not config.example_sql_queries:
            warnings.append("No example SQL queries - consider adding examples")
            score -= 10

        # Check if space_name and description are meaningful
        if len(config.space_name) < 5:
            warnings.append("Space name is very short - use descriptive names")
            score -= 5

        if len(config.description) < 20:
            warnings.append("Description is very short - provide more context")
            score -= 5

        return errors, warnings, max(0, score)

    def _validate_sql(self, config: GenieSpaceConfig) -> tuple[list[str], list[str], int]:
        """Validate SQL in configuration.

        Returns:
            Tuple of (errors, warnings, score)
        """
        errors = []
        warnings = []
        score = 100

        # Validate example SQL queries
        for i, example in enumerate(config.example_sql_queries):
            try:
                self._validate_sql_syntax(example.sql_query)
            except Exception as e:
                errors.append(f"Example query #{i+1} has invalid SQL: {str(e)}")
                score -= 15

        # Validate SQL snippets
        if config.sql_snippets:
            # Validate filters
            for i, filt in enumerate(config.sql_snippets.filters):
                try:
                    self._validate_sql_syntax(filt.sql)
                except Exception as e:
                    errors.append(f"Filter #{i+1} has invalid SQL: {str(e)}")
                    score -= 5

            # Validate expressions
            for i, expr in enumerate(config.sql_snippets.expressions):
                try:
                    self._validate_sql_syntax(expr.sql)
                except Exception as e:
                    errors.append(f"Expression '{expr.alias}' has invalid SQL: {str(e)}")
                    score -= 5

            # Validate measures
            for i, measure in enumerate(config.sql_snippets.measures):
                try:
                    self._validate_sql_syntax(measure.sql)
                except Exception as e:
                    errors.append(f"Measure '{measure.alias}' has invalid SQL: {str(e)}")
                    score -= 5

        return errors, warnings, max(0, score)

    def _validate_sql_syntax(self, sql: str) -> None:
        """Validate SQL syntax using sqlparse.

        Args:
            sql: SQL string to validate

        Raises:
            ValueError: If SQL is invalid
        """
        if not sql or not sql.strip():
            raise ValueError("Empty SQL query")

        # Parse with sqlparse
        parsed = sqlparse.parse(sql)
        if not parsed:
            raise ValueError("Failed to parse SQL query")

        # Check for balanced parentheses
        if sql.count("(") != sql.count(")"):
            raise ValueError("Unbalanced parentheses")

        # Check for balanced quotes
        single_quotes = sql.count("'") - sql.count("\\'")
        if single_quotes % 2 != 0:
            raise ValueError("Unbalanced single quotes")

    def _check_instruction_quality(self, config: GenieSpaceConfig) -> tuple[list[str], int]:
        """Check instruction quality.

        Returns:
            Tuple of (warnings, score)
        """
        warnings = []
        score = 100

        if not config.instructions:
            return warnings, score

        vague_terms = ["appropriate", "relevant", "good", "properly", "as needed"]

        for i, instruction in enumerate(config.instructions):
            content_lower = instruction.content.lower()

            # Check for vague terms
            found_vague = [term for term in vague_terms if term in content_lower]
            if found_vague:
                warnings.append(
                    f"Instruction #{i+1} contains vague terms: {', '.join(found_vague)}"
                )
                score -= 5

            # Check length
            word_count = len(instruction.content.split())
            if word_count < 10:
                warnings.append(f"Instruction #{i+1} is very short ({word_count} words)")
                score -= 3

            # Check for specificity (backticked column names)
            if "`" not in instruction.content:
                warnings.append(
                    f"Instruction #{i+1} lacks specific column/table references (use backticks)"
                )
                score -= 3

        return warnings, max(0, score)

    def validate_json_string(self, json_string: str) -> ValidationReport:
        """Validate a JSON string as a Genie configuration.

        Args:
            json_string: JSON string to validate

        Returns:
            ValidationReport with validation results
        """
        try:
            config_dict = json.loads(json_string)
        except json.JSONDecodeError as e:
            return ValidationReport(
                valid=False, errors=[f"Invalid JSON: {str(e)}"], warnings=[], score=0
            )

        return self.validate_config(config_dict)
