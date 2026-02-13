"""
Adapter para escribir reportes en formato CSV.
Implementa ReportWriterPort para generar archivos CSV tabular desde análisis estructurados.
"""

import logging
import csv
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CSVReportWriter:
    """Escribe reportes en formato CSV"""
    
    def write_report(
        self,
        run_id: str,
        report_content: str,
        output_dir: str,
        analysis: Optional[Dict] = None
    ) -> str:
        """
        Escribe el reporte en formato CSV.
        Usa la información del análisis estructurado para generar una tabla.
        
        Args:
            run_id: Identificador único de la ejecución
            report_content: Contenido del reporte (usado como comentario cabecera)
            output_dir: Directorio de salida
            analysis: Análisis estructurado con summary y error_groups
        
        Returns:
            Path del archivo generado
        
        Raises:
            IOError: Si hay error de escritura
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{run_id}_report.csv"
        file_path = output_path / filename
        
        logger.debug(f"Escribiendo reporte CSV a {file_path}")
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Escribir encabezados
                writer.writerow(["Metric", "Value"])
                
                # Escribir resumen si está disponible
                if analysis and "summary" in analysis:
                    summary = analysis["summary"]
                    for key, value in summary.items():
                        writer.writerow([key, value])
                
                # Escribir grupos de errores si están disponibles
                if analysis and "error_groups" in analysis:
                    writer.writerow([])  # Fila vacía para separación
                    writer.writerow(["Error Type", "Count", "First Occurrence"])
                    
                    for error_group in analysis["error_groups"]:
                        exception = error_group.get("exception", "Unknown")
                        count = error_group.get("count", 0)
                        first_ts = error_group.get("first_ts", "N/A")
                        
                        writer.writerow([exception, count, first_ts])
            
            logger.info(f"Reporte CSV generado: {file_path}")
            return str(file_path.absolute())
        
        except Exception as e:
            logger.error(f"Error al escribir reporte CSV: {e}")
            raise IOError(f"Error al escribir archivo CSV: {e}") from e
