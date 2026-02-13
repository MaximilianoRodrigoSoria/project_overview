"""
Exporter de reportes en formato Markdown.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from ..ports.report_exporter_port import ReportExporterPort


logger = logging.getLogger(__name__)


class MarkdownExporter(ReportExporterPort):
    """Exporta reportes en formato Markdown (.md)"""
    
    def export(
        self,
        output_dir: str,
        output_filename: str,
        report_content: str,
        analysis: Optional[Dict] = None
    ) -> str:
        """
        Exporta el reporte en formato Markdown.
        
        Args:
            output_dir: Directorio de salida
            output_filename: Nombre del archivo (sin extensión)
            report_content: Contenido del reporte en Markdown
            analysis: Análisis estructurado (no usado en markdown)
        
        Returns:
            Path absoluto del archivo generado
        
        Raises:
            IOError: Si hay error de escritura
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{output_filename}.md"
        file_path = output_path / filename
        
        logger.debug(f"Exportando reporte Markdown a {file_path}")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Reporte Markdown exportado: {file_path}")
            return str(file_path.absolute())
        
        except Exception as e:
            logger.error(f"Error al exportar reporte Markdown: {e}")
            raise IOError(f"Error al escribir archivo Markdown: {e}") from e
