"""
Puerto para exportación de reportes a diferentes formatos.
Define la interfaz común para todos los exporters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class ReportExporterPort(ABC):
    """
    Interfaz para exporters de reportes.
    Cada implementación exporta a un formato específico.
    """
    
    @abstractmethod
    def export(
        self,
        output_dir: str,
        output_filename: str,
        report_content: str,
        analysis: Optional[Dict] = None
    ) -> str:
        """
        Exporta el reporte al formato específico.
        
        Args:
            output_dir: Directorio donde guardar el archivo
            output_filename: Nombre del archivo (sin extensión)
            report_content: Contenido del reporte (usualmente en Markdown)
            analysis: Análisis estructurado (opcional, para formatos tabulares)
        
        Returns:
            Path absoluto del archivo generado
        
        Raises:
            IOError: Si hay error de escritura
            ValueError: Si faltan datos requeridos
        """
        pass
