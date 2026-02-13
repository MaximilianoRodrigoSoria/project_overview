"""
Exporter de reportes en formato CSV.
Genera tablas con información del análisis estructurado.
"""

import logging
import csv
from pathlib import Path
from typing import Dict, Optional

from ..ports.report_exporter_port import ReportExporterPort


logger = logging.getLogger(__name__)


class CsvExporter(ReportExporterPort):
    """Exporta reportes en formato CSV tabular"""
    
    def export(
        self,
        output_dir: str,
        output_filename: str,
        report_content: str,
        analysis: Optional[Dict] = None
    ) -> str:
        """
        Exporta el reporte en formato CSV.
        Genera tabla con timestamp, level, component, message, probable_cause, recommendation.
        
        Args:
            output_dir: Directorio de salida
            output_filename: Nombre del archivo (sin extensión)
            report_content: Contenido del reporte (usado para recomendaciones)
            analysis: Análisis estructurado (requerido para CSV)
        
        Returns:
            Path absoluto del archivo generado
        
        Raises:
            IOError: Si hay error de escritura
            ValueError: Si no hay analysis disponible
        """
        if analysis is None:
            raise ValueError("Análisis estructurado requerido para exportar a CSV")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{output_filename}.csv"
        file_path = output_path / filename
        
        logger.debug(f"Exportando reporte CSV a {file_path}")
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Encabezados según especificación
                writer.writerow([
                    "timestamp",
                    "level",
                    "component",
                    "message",
                    "probable_cause",
                    "recommendation"
                ])
                
                # Escribir errores como filas
                if "error_groups" in analysis:
                    for error_group in analysis["error_groups"]:
                        timestamp = error_group.get("first_ts", "N/A")
                        level = "ERROR"
                        component = error_group.get("logger", "Unknown")
                        exception = error_group.get("exception", "Unknown")
                        count = error_group.get("count", 0)
                        message = f"{exception} ({count} ocurrencias)"
                        
                        # Extraer causa probable del top_frame si existe
                        probable_cause = ""
                        if "top_frame" in error_group and error_group["top_frame"]:
                            frame = error_group["top_frame"]
                            probable_cause = f"{frame.get('file', 'unknown')}:{frame.get('line', '?')}"
                        
                        # Recomendación genérica basada en el tipo de error
                        recommendation = self._generate_recommendation(exception)
                        
                        writer.writerow([
                            timestamp,
                            level,
                            component,
                            message,
                            probable_cause,
                            recommendation
                        ])
                
                # Escribir warnings como filas
                if "warnings" in analysis:
                    for warning in analysis["warnings"][:20]:  # Limitar a 20
                        timestamp = warning.get("timestamp", "N/A")
                        level = "WARN"
                        component = warning.get("logger", "Unknown")
                        message = warning.get("message", "")
                        probable_cause = "Ver logs para contexto"
                        recommendation = "Revisar configuración o dependencias"
                        
                        writer.writerow([
                            timestamp,
                            level,
                            component,
                            message,
                            probable_cause,
                            recommendation
                        ])
            
            logger.info(f"Reporte CSV exportado: {file_path}")
            return str(file_path.absolute())
        
        except Exception as e:
            logger.error(f"Error al exportar reporte CSV: {e}")
            raise IOError(f"Error al escribir archivo CSV: {e}") from e
    
    def _generate_recommendation(self, exception_name: str) -> str:
        """
        Genera una recomendación básica según el tipo de excepción.
        
        Args:
            exception_name: Nombre de la excepción
        
        Returns:
            Recomendación textual
        """
        recommendations = {
            "NullPointerException": "Verificar inicialización de objetos y referencias nulas",
            "FileNotFoundException": "Verificar rutas y permisos de archivos",
            "ConnectionException": "Revisar conectividad de red y configuración de endpoints",
            "TimeoutException": "Aumentar timeouts o mejorar performance del servicio",
            "SQLException": "Verificar queries y conexiones a base de datos",
            "IOException": "Revisar operaciones de I/O y permisos de sistema",
            "IllegalArgumentException": "Validar parámetros de entrada",
            "OutOfMemoryError": "Aumentar heap size o revisar memory leaks",
        }
        
        for key, recommendation in recommendations.items():
            if key.lower() in exception_name.lower():
                return recommendation
        
        return "Revisar stacktrace y contexto del error"
