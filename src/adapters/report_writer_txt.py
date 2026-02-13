"""
Adapter para escribir reportes en formato texto plano (.txt).
Implementa ReportWriterPort para generar archivos de texto simples.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TextReportWriter:
    """Escribe reportes en formato texto plano (.txt)"""
    
    def write_report(
        self,
        run_id: str,
        report_content: str,
        output_dir: str,
        analysis: Optional[Dict] = None
    ) -> str:
        """
        Escribe el reporte en formato texto plano.
        
        Args:
            run_id: Identificador único de la ejecución
            report_content: Contenido del reporte
            output_dir: Directorio de salida
            analysis: Análisis estructurado (ignorado para txt)
        
        Returns:
            Path del archivo generado
        
        Raises:
            IOError: Si hay error de escritura
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{run_id}_report.txt"
        file_path = output_path / filename
        
        logger.debug(f"Escribiendo reporte de texto a {file_path}")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Reporte de texto generado: {file_path}")
            return str(file_path.absolute())
        
        except Exception as e:
            logger.error(f"Error al escribir reporte de texto: {e}")
            raise IOError(f"Error al escribir archivo: {e}") from e
