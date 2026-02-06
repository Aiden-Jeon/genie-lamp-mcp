"""Analyze Genie space configuration quality and health."""

from typing import Optional
from datetime import datetime, timedelta


class ConfigAnalyzer:
    """Analyze Genie space configuration quality and generate health reports."""

    def health_score(
        self,
        config: dict,
        conversation_count: int = 0,
        last_activity: Optional[datetime] = None
    ) -> tuple[int, list[str]]:
        """Calculate health score (0-100) and recommendations.

        Args:
            config: GenieSpaceConfig dict.
            conversation_count: Number of conversations in last 30 days.
            last_activity: Timestamp of last activity.

        Returns:
            Tuple of (score, recommendations).
        """
        score = 100
        recommendations = []

        # Configuration quality (60% of score)
        config_score, config_recs = self._analyze_config_quality(config)
        score = int(score * 0.6 * (config_score / 100))
        recommendations.extend(config_recs)

        # Activity level (40% of score)
        activity_score, activity_recs = self._analyze_activity(
            conversation_count, last_activity
        )
        score += int(100 * 0.4 * (activity_score / 100))
        recommendations.extend(activity_recs)

        return (score, recommendations)

    def _analyze_config_quality(self, config: dict) -> tuple[int, list[str]]:
        """Analyze configuration quality.

        Args:
            config: GenieSpaceConfig dict.

        Returns:
            Tuple of (score, recommendations).
        """
        score = 100
        recommendations = []

        # Table checks
        table_count = len(config.get("tables", []))
        if table_count == 0:
            score -= 40
            recommendations.append("❌ **Critical:** Add at least one table to the space")
        elif table_count > 10:
            score -= 10
            recommendations.append("⚠️ Consider splitting into multiple spaces (10+ tables)")

        # Instruction checks
        instruction_count = len(config.get("instructions", []))
        if instruction_count == 0:
            score -= 20
            recommendations.append("❌ **Critical:** Add instructions to guide Genie")
        elif instruction_count < 5:
            score -= 10
            recommendations.append(
                f"⚠️ Add more instructions (current: {instruction_count}, recommend: 5+)"
            )

        # Example query checks
        example_count = len(config.get("example_sql_queries", []))
        if example_count < 3:
            score -= 15
            recommendations.append(
                f"⚠️ Add example queries (current: {example_count}, recommend: 5+)"
            )

        # SQL snippet checks
        snippets = config.get("sql_snippets", {})
        measure_count = len(snippets.get("measures", []))
        expression_count = len(snippets.get("expressions", []))

        if measure_count == 0 and expression_count == 0:
            score -= 15
            recommendations.append("⚠️ Add SQL measures or expressions for common metrics")

        # Join checks
        if table_count > 1:
            join_count = len(config.get("join_specifications", []))
            if join_count == 0:
                score -= 10
                recommendations.append("⚠️ Define joins to connect tables")

        return (max(0, score), recommendations)

    def _analyze_activity(
        self,
        conversation_count: int,
        last_activity: Optional[datetime]
    ) -> tuple[int, list[str]]:
        """Analyze space activity level.

        Args:
            conversation_count: Number of conversations in last 30 days.
            last_activity: Timestamp of last activity.

        Returns:
            Tuple of (score, recommendations).
        """
        score = 100
        recommendations = []

        # Conversation activity
        if conversation_count == 0:
            score -= 40
            recommendations.append("⚠️ No recent activity - consider adding example queries to encourage use")
        elif conversation_count < 5:
            score -= 20
            recommendations.append(
                f"ℹ️ Low activity ({conversation_count} conversations in 30 days)"
            )

        # Recency
        if last_activity:
            days_since = (datetime.now() - last_activity).days
            if days_since > 30:
                score -= 30
                recommendations.append(f"⚠️ Inactive for {days_since} days")
            elif days_since > 7:
                score -= 10
                recommendations.append(f"ℹ️ Last active {days_since} days ago")

        return (max(0, score), recommendations)

    def generate_health_report(
        self,
        space_name: str,
        config: dict,
        conversation_count: int = 0,
        last_activity: Optional[datetime] = None
    ) -> str:
        """Generate a comprehensive health report.

        Args:
            space_name: Name of the space.
            config: GenieSpaceConfig dict.
            conversation_count: Number of conversations in last 30 days.
            last_activity: Timestamp of last activity.

        Returns:
            Formatted markdown health report.
        """
        score, recommendations = self.health_score(
            config, conversation_count, last_activity
        )

        # Build report
        output = f"# 🏥 Space Health Report: {space_name}\n\n"
        output += f"## Overall Score: {score}/100\n\n"

        # Score interpretation
        if score >= 90:
            output += "✅ **Excellent** - Space is well-configured and active\n\n"
        elif score >= 70:
            output += "✅ **Good** - Space is functional with room for improvement\n\n"
        elif score >= 50:
            output += "⚠️ **Fair** - Space needs attention\n\n"
        else:
            output += "❌ **Poor** - Space requires immediate attention\n\n"

        # Configuration quality
        output += "## Configuration Quality\n\n"
        output += self._format_config_metrics(config)
        output += "\n"

        # Activity metrics
        output += "## Activity\n\n"
        output += self._format_activity_metrics(conversation_count, last_activity)
        output += "\n"

        # Recommendations
        if recommendations:
            output += "## Recommendations\n\n"
            for rec in recommendations:
                output += f"- {rec}\n"
            output += "\n"

        # Next steps
        output += "## Next Steps\n\n"
        output += "- Export config: Use `/inspect` with mode='export'\n"
        output += "- Update config: Use `/bulk` to add instructions/snippets\n"
        output += "- Test queries: Use `/ask` to verify functionality\n"

        return output

    def _format_config_metrics(self, config: dict) -> str:
        """Format configuration metrics section.

        Args:
            config: GenieSpaceConfig dict.

        Returns:
            Formatted markdown string.
        """
        table_count = len(config.get("tables", []))
        instruction_count = len(config.get("instructions", []))
        example_count = len(config.get("example_sql_queries", []))
        join_count = len(config.get("join_specifications", []))

        snippets = config.get("sql_snippets", {})
        measure_count = len(snippets.get("measures", []))
        expression_count = len(snippets.get("expressions", []))
        filter_count = len(snippets.get("filters", []))

        output = ""
        output += self._format_metric("Tables", table_count, 1, 10)
        output += self._format_metric("Instructions", instruction_count, 5, None)
        output += self._format_metric("Example Queries", example_count, 5, None)
        output += self._format_metric("SQL Measures", measure_count, 1, None)
        output += self._format_metric("SQL Expressions", expression_count, 1, None)
        output += self._format_metric("SQL Filters", filter_count, 0, None)

        if table_count > 1:
            output += self._format_metric("Join Specifications", join_count, table_count - 1, None)

        return output

    def _format_metric(
        self,
        name: str,
        value: int,
        min_recommended: int,
        max_recommended: Optional[int]
    ) -> str:
        """Format a single metric line.

        Args:
            name: Metric name.
            value: Current value.
            min_recommended: Minimum recommended value.
            max_recommended: Maximum recommended value (None if no max).

        Returns:
            Formatted metric line.
        """
        icon = "✅" if value >= min_recommended else "⚠️"

        if max_recommended and value > max_recommended:
            icon = "⚠️"
            note = f" (recommend {min_recommended}-{max_recommended})"
        elif value < min_recommended:
            note = f" (recommend {min_recommended}+)"
        else:
            note = ""

        return f"{icon} **{name}:** {value}{note}\n"

    def _format_activity_metrics(
        self,
        conversation_count: int,
        last_activity: Optional[datetime]
    ) -> str:
        """Format activity metrics section.

        Args:
            conversation_count: Number of conversations.
            last_activity: Last activity timestamp.

        Returns:
            Formatted markdown string.
        """
        output = ""

        # Conversation count
        if conversation_count == 0:
            output += "⚠️ **Conversations:** No activity in last 30 days\n"
        elif conversation_count < 5:
            output += f"ℹ️ **Conversations:** {conversation_count} in last 30 days (low activity)\n"
        else:
            output += f"✅ **Conversations:** {conversation_count} in last 30 days (active)\n"

        # Last activity
        if last_activity:
            days_since = (datetime.now() - last_activity).days
            if days_since == 0:
                output += "✅ **Last Activity:** Today\n"
            elif days_since == 1:
                output += "✅ **Last Activity:** Yesterday\n"
            elif days_since < 7:
                output += f"✅ **Last Activity:** {days_since} days ago\n"
            elif days_since < 30:
                output += f"ℹ️ **Last Activity:** {days_since} days ago\n"
            else:
                output += f"⚠️ **Last Activity:** {days_since} days ago (inactive)\n"
        else:
            output += "ℹ️ **Last Activity:** Unknown\n"

        return output
