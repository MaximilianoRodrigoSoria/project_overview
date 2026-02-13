"""
Exporter de reportes en formato texto plano (.txt).
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from ..ports.report_exporter_port import ReportExporterPort


logger = logging.getLogger(__name__)


class TxtExporter(ReportExporterPort):
    """Exporta reportes en formato texto plano"""
    
    def export(
        self,
        output_dir: str,
        output_filename: str,
        report_content: str,
        analysis: Optional[Dict] = None
    ) -> str:
        """
        Exporta el reporte en formato texto plano.
        Convierte Markdown a texto simple si es necesario.
        
        Args:
            output_dir: Directorio de salida
            output_filename: Nombre del archivo (sin extensión)
            report_content: Contenido del reporte
            analysis: Análisis estructurado (opcional, para enriquecer)
        
        Returns:
            Path absoluto del archivo generado
        
        Raises:
            IOError: Si hay error de escritura
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{output_filename}.txt"
        file_path = output_path / filename
        
        logger.debug(f"Exportando reporte TXT a {file_path}")
        
        try:
            # Convertir markdown a texto plano (remover marcas de formato básicas)
            plain_text = self._markdown_to_plain(report_content)
            
            # Agregar resumen al inicio si hay analysis
            if analysis and "summary" in analysis:
                summary_text = self._format_summary(analysis["summary"])
                plain_text = summary_text + "\n\n" + plain_text
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(plain_text)
            
            logger.info(f"Reporte TXT exportado: {file_path}")
            return str(file_path.absolute())
        
        except Exception as e:
            logger.error(f"Error al exportar reporte TXT: {e}")
            raise IOError(f"Error al escribir archivo TXT: {e}") from e
    
    def _markdown_to_plain(self, markdown_text: str) -> str:
        """
        Convierte Markdown básico a texto plano.
        
        Args:
            markdown_text: Texto en formato Markdown
        
        Returns:
            Texto plano sin marcas de formato
        """
        text = markdown_text
        
        # Remover marcas de encabezados
        text = text.replace('# ', '')
        text = text.replace('## ', '')
        text = text.replace('### ', '')
        text = text.replace('#### ', '')
        
        # Remover énfasis
        text = text.replace('**', '')
        text = text.replace('__', '')
        text = text.replace('*', '')
        text = text.replace('_', '')
        
        # Remover código inline
        text = text.replace('`', '')
        
        # Remover bullets
        text = text.replace('- ', '  • ')
        
        return text
    
    def _format_summary(self, summary: Dict) -> str:
        """
        Formatea el resumen para texto plano.
        
        Args:
            summary: Diccionario con el resumen
        
        Returns:
            Resumen formateado
        """
        lines = ["=" * 60, "RESUMEN DEL ANÁLISIS", "=" * 60, ""]
        
        for key, value in summary.items():
            label = key.replace('_', ' ').title()
            lines.append(f"{label}: {value}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
