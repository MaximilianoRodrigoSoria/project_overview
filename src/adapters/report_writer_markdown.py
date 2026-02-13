"""Adapter for Markdown report bytes."""

from typing import Dict


class MarkdownBytesWriter:
    """Generate Markdown report content as bytes for API downloads."""

    def write(self, report_data: Dict) -> bytes:
        """
        Write report data as Markdown bytes.
        
        Supports both:
        - Generic reports with deterministic + narrative
        - Code quality reports with metrics + narrative
        """
        lines = []
        
        # Check if this is a code quality report
        if "technology" in report_data:
            lines.extend(self._write_code_quality_report(report_data))
        else:
            lines.extend(self._write_generic_report(report_data))
        
        return "\n".join(lines).encode("utf-8")
    
    def _write_code_quality_report(self, report_data: Dict) -> list:
        """Write code quality report in Markdown format."""
        lines = []
        
        # Header
        lines.append(f"# Reporte de Calidad de Código")
        lines.append("")
        lines.append(f"**Proyecto:** {report_data.get('report_name', 'N/A')}")
        lines.append(f"**Ruta:** {report_data.get('project_path', 'N/A')}")
        lines.append(f"**Tecnología:** {report_data.get('technology', 'N/A')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Metrics section
        metrics = report_data.get("metrics", {})
        if metrics:
            lines.append("## Métricas del Proyecto")
            lines.append("")
            lines.append(f"- **Total de archivos:** {metrics.get('total_files', 0)}")
            lines.append(f"- **Total de líneas:** {metrics.get('total_lines', 0)}")
            lines.append(f"- **Promedio líneas/archivo:** {metrics.get('avg_lines_per_file', 0):.1f}")
            
            # Add tech-specific metrics
            technology = report_data.get('technology', '')
            if technology == 'spring-boot':
                lines.append(f"- **Clases:** {metrics.get('num_classes', 0)}")
                lines.append(f"- **Controladores REST:** {metrics.get('num_rest_controllers', 0)}")
                lines.append(f"- **Servicios:** {metrics.get('num_services', 0)}")
                lines.append(f"- **Repositorios:** {metrics.get('num_repositories', 0)}")
            elif technology == 'angular':
                lines.append(f"- **Componentes:** {metrics.get('num_components', 0)}")
                lines.append(f"- **Servicios:** {metrics.get('num_services', 0)}")
                lines.append(f"- **Tamaño estimado bundle:** {metrics.get('estimated_bundle_size_kb', 0)} KB")
            elif technology == 'python':
                lines.append(f"- **Módulos:** {metrics.get('num_modules', 0)}")
                lines.append(f"- **Funciones:** {metrics.get('num_functions', 0)}")
                lines.append(f"- **Clases:** {metrics.get('num_classes', 0)}")
            
            lines.append("")
        
        # LLM Narrative section - this is the key part
        narrative = report_data.get("narrative")
        if narrative:
            # Get the full summary which contains the complete LLM-generated report
            summary = narrative.get("summary", "")
            if summary:
                lines.append("---")
                lines.append("")
                # The summary contains the full markdown report from LLM
                lines.append(summary)
                lines.append("")
            
            # Add recommendations if extracted
            recommendations = narrative.get("recommendations", [])
            if recommendations and not summary:  # Only if summary didn't include them
                lines.append("## Recomendaciones")
                lines.append("")
                for rec in recommendations:
                    lines.append(f"- {rec}")
                lines.append("")
            
            # Add insights if extracted
            insights = narrative.get("insights", [])
            if insights and not summary:  # Only if summary didn't include them
                lines.append("## Insights Técnicos")
                lines.append("")
                for insight in insights:
                    lines.append(f"- {insight}")
                lines.append("")
        
        return lines
    
    def _write_generic_report(self, report_data: Dict) -> list:
        """Write generic report in Markdown format."""
        lines = []
        
        lines.append("# Report")
        lines.append("")
        
        # Deterministic Analysis
        lines.append("## Deterministic Analysis")
        lines.append("")
        deterministic = report_data.get("deterministic", {})
        for key, value in deterministic.items():
            lines.append(f"- **{key}**: {value}")
        lines.append("")
        
        # Narrative
        narrative = report_data.get("narrative")
        if narrative:
            lines.append("## Narrative")
            lines.append("")
            summary = narrative.get("summary", "")
            if summary:
                lines.append(summary)
                lines.append("")
            
            insights = narrative.get("insights", [])
            if insights:
                lines.append("### Insights")
                lines.append("")
                for insight in insights:
                    lines.append(f"- {insight}")
                lines.append("")
        
        return lines
