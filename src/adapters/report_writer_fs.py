"""
Adapter de escritura de reportes al filesystem.
Implementa ReportWriterPort para escribir archivos locales.
Registra y despacha a format-specific writers (excel, txt, csv, doc).
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from ..ports.report_writer_port import ReportWriterPort
from ..config.settings import settings
from ..config.constants import Constants
from .report_writer_excel import ExcelReportWriter
from .report_writer_txt import TextReportWriter
from .report_writer_csv import CSVReportWriter
from .report_writer_doc import DocReportWriter


logger = logging.getLogger(__name__)


class FileSystemReportWriter(ReportWriterPort):
    """
    Escribe reportes y análisis en el filesystem local.
    Despacha a writers específicos según el formato solicitado.
    """
    
    def __init__(self):
        """Inicializa el writer con todos los format writers disponibles"""
        self.reports_dir = settings.REPORTS_DIR
        self.analysis_dir = settings.ANALYSIS_DIR
        
        # Registrar todos los writers disponibles
        self.writers = {
            Constants.REPORT_FORMAT_EXCEL: ExcelReportWriter(self.reports_dir),
            Constants.REPORT_FORMAT_TXT: TextReportWriter(),
            Constants.REPORT_FORMAT_CSV: CSVReportWriter(),
            Constants.REPORT_FORMAT_DOC: DocReportWriter(),
        }
        
        logger.debug(
            f"FileSystemReportWriter: "
            f"reports={self.reports_dir}, analysis={self.analysis_dir}, "
            f"formats={list(self.writers.keys())}"
        )
    
    def write_analysis(self, run_id: str, analysis: Dict) -> str:
        """
        Escribe el análisis en formato JSON.
        
        Args:
            run_id: Identificador de la ejecución
            analysis: Diccionario con el análisis
        
        Returns:
            Path absoluto del archivo generado
        """
        # Asegurar que existe el directorio
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Construir path del archivo
        filename = f"{run_id}{Constants.ANALYSIS_FILE_EXTENSION}"
        filepath = self.analysis_dir / filename
        
        logger.debug(f"Escribiendo análisis: {filepath}")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Análisis guardado: {filepath}")
            return str(filepath.resolve())
            
        except Exception as e:
            logger.error(f"Error al escribir análisis: {e}")
            raise IOError(f"{Constants.ERROR_WRITE_FAILED}: {e}") from e
    
    def write_report(
        self,
        run_id: str,
        report_content: str,
        report_format: str = "markdown",
        analysis: Optional[Dict] = None
    ) -> str:
        """
        Escribe el reporte en el formato indicado.
        
        Args:
            run_id: Identificador de la ejecución
            report_content: Contenido del reporte
            report_format: Formato de salida (excel, txt, csv, doc, markdown)
            analysis: Analisis estructurado para reportes tabulares
        
        Returns:
            Path absoluto del archivo generado
        
        Raises:
            ValueError: Si el formato no es soportado
            IOError: Si hay error de escritura
        """
        # Normalizar el nombre del formato
        format_lower = report_format.lower() if report_format else "markdown"
        
        # Comprobar si el formato está registrado
        if format_lower in self.writers:
            writer = self.writers[format_lower]
            return writer.write_report(
                run_id=run_id,
                report_content=report_content,
                output_dir=str(self.reports_dir),
                analysis=analysis
            )
        
        # Si no es un formato registrado, asumir markdown
        if format_lower in ["markdown", "md", "both"]:
            return self._write_markdown(run_id, report_content)
        
        raise ValueError(f"Formato no soportado: {report_format}")
    
    def _write_markdown(self, run_id: str, report_content: str) -> str:
        """
        Escribe el reporte en formato Markdown.
        
        Args:
            run_id: Identificador de la ejecución
            report_content: Contenido en Markdown
        
        Returns:
            Path al archivo generado
        """
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{run_id}{Constants.REPORT_FILE_EXTENSION}"
        filepath = self.reports_dir / filename

        logger.debug("Escribiendo reporte Markdown: %s", filepath)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report_content)
            
            logger.info(f"Reporte Markdown generado: {filepath}")
            return str(filepath.resolve())
            
        except Exception as e:
            logger.error(f"Error al escribir reporte Markdown: {e}")
            raise IOError(f"{Constants.ERROR_WRITE_FAILED}: {e}") from e

            logger.info("Reporte guardado: %s", filepath)
            return str(filepath.resolve())
        except Exception as e:
            logger.error("Error al escribir reporte: %s", e)
            raise IOError(f"{Constants.ERROR_WRITE_FAILED}: {e}") from e
