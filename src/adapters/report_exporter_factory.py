"""
Factory para crear exporters de reportes según el formato solicitado.
Implementa el patrón Factory para desacoplar la creación de exporters.
Usa imports lazy para evitar errores de dependencias no instaladas.
"""

import logging
from typing import Dict

from ..domain.enums import OutputFormat
from ..ports.report_exporter_port import ReportExporterPort


logger = logging.getLogger(__name__)


class ReportExporterFactory:
    """
    Factory para crear exporters de reportes.
    Centraliza la creación de exportes según el formato.
    Usa lazy imports para cargar solo los exporters necesarios.
    """
    
    # Registry de módulos y clases de exporters (lazy loading)
    _exporter_modules: Dict[OutputFormat, tuple] = {
        OutputFormat.MARKDOWN: ('.report_exporter_markdown', 'MarkdownExporter'),
        OutputFormat.CSV: ('.report_exporter_csv', 'CsvExporter'),
        OutputFormat.TXT: ('.report_exporter_txt', 'TxtExporter'),
        OutputFormat.EXCEL: ('.report_exporter_excel', 'ExcelExporter'),
        OutputFormat.DOC: ('.report_exporter_doc', 'DocExporter'),
    }
    
    @classmethod
    def create(cls, output_format: OutputFormat) -> ReportExporterPort:
        """
        Crea una instancia del exporter apropiado según el formato.
        Usa lazy import para cargar solo el exporter necesario.
        
        Args:
            output_format: Formato de salida requerido
        
        Returns:
            Instancia del exporter correspondiente
        
        Raises:
            ValueError: Si el formato no está soportado
            ImportError: Si faltan dependencias para el formato
        """
        if output_format not in cls._exporter_modules:
            raise ValueError(
                f"Formato no soportado: {output_format}. "
                f"Formatos disponibles: {', '.join([f.value for f in cls._exporter_modules.keys()])}"
            )
        
        module_name, class_name = cls._exporter_modules[output_format]
        logger.debug(f"Creando exporter para formato: {output_format.value}")
        
        try:
            # Lazy import: importar solo cuando se necesita
            from importlib import import_module
            module = import_module(module_name, package=__package__)
            exporter_class = getattr(module, class_name)
            
            return exporter_class()
            
        except ImportError as e:
            error_msg = (
                f"No se puede crear exporter para formato '{output_format.value}'. "
                f"Falta instalar dependencias. Error: {e}"
            )
            logger.error(error_msg)
            raise ImportError(error_msg) from e
    
    @classmethod
    def register(cls, output_format: OutputFormat, module_path: str, class_name: str):
        """
        Registra un nuevo exporter en el factory.
        Útil para extender con formatos personalizados.
        
        Args:
            output_format: Formato que maneja el exporter
            module_path: Path del módulo (ej: '.report_exporter_custom')
            class_name: Nombre de la clase del exporter
        """
        logger.info(f"Registrando exporter para formato: {output_format.value}")
        cls._exporter_modules[output_format] = (module_path, class_name)
    
    @classmethod
    def supported_formats(cls) -> list:
        """
        Retorna la lista de formatos soportados.
        
        Returns:
            Lista de OutputFormat soportados
        """
        return list(cls._exporter_modules.keys())
