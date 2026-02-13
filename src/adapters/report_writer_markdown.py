"""Adapter for Markdown report bytes."""

from typing import Dict


class MarkdownBytesWriter:
    """Generate Markdown report content as bytes for API downloads."""

    def write(self, report_data: Dict) -> bytes:
        lines = ["# Report", "", "## Deterministic Analysis"]
        deterministic = report_data.get("deterministic", {})
        for key, value in deterministic.items():
            lines.append(f"- **{key}**: {value}")

        narrative = report_data.get("narrative")
        if narrative:
            lines.append("")
            lines.append("## Narrative")
            lines.append(narrative.get("summary", ""))
            insights = narrative.get("insights", [])
            if insights:
                lines.append("")
                lines.append("### Insights")
                for insight in insights:
                    lines.append(f"- {insight}")

        return "\n".join(lines).encode("utf-8")
