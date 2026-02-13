"""
Casos de uso del dominio log_analyzer.
Contiene la lógica de negocio principal.
"""

import json
import logging
from typing import Optional, List, Dict
from uuid import uuid4

from .model import LogAnalysis, ReportOutput, LogFile
from ..ports.log_reader_port import LogReaderPort
from ..ports.analyzer_port import AnalyzerPort
from ..ports.llm_port import LLMPort
from ..ports.report_writer_port import ReportWriterPort
from ..ports.cache_port import CachePort
from ..config.settings import settings
from ..config.constants import Constants
from ..config.logging_config import log_with_run_id
from ..adapters.cache_key import build_cache_key


logger = logging.getLogger(__name__)


class ListLogsUseCase:
    """
    Caso de uso: Listar archivos de logs disponibles.
    
    Flujo:
    1. Consultar directorio de datasets
    2. Retornar lista de archivos .txt con metadatos
    """
    
    def __init__(self, log_reader: LogReaderPort):
        self.log_reader = log_reader
    
    def execute(self, datasets_dir: str) -> Dict[str, any]:
        """
        Ejecuta el caso de uso de listado.
        
        Args:
            datasets_dir: Ruta del directorio de datasets
        
        Returns:
            Dict con "files": List[LogFile] y "count": int
        
        Raises:
            FileNotFoundError: Si el directorio no existe
            IOError: Si hay error de lectura del directorio
        """
        logger.info(f"Listando logs en {datasets_dir}")
        
        try:
            # Obtener lista de archivos del log reader
            log_files = self.log_reader.list_logs(datasets_dir)
            
            logger.info(f"Se encontraron {len(log_files)} archivos de logs")
            
            return {
                "files": log_files,
                "count": len(log_files)
            }
        
        except Exception as e:
            logger.error(f"Error listando logs: {e}")
            raise


class GenerateReportUseCase:
    """
    Caso de uso principal: Generar reporte de análisis de logs.
    
    Flujo:
    1. Leer logs (desde texto o archivo)
    2. Analizar con analyzer determinista (regex)
    3. Construir prompt robusto para LLM
    4. Llamar a LLM para generar reporte Markdown
    5. Escribir archivos de salida (JSON + MD)
    6. Retornar paths y resumen
    """
    
    def __init__(
        self,
        log_reader: LogReaderPort,
        analyzer: AnalyzerPort,
        llm: LLMPort,
        report_writer: ReportWriterPort,
        cache: Optional[CachePort] = None
    ):
        self.log_reader = log_reader
        self.analyzer = analyzer
        self.llm = llm
        self.report_writer = report_writer
        self.cache = cache
    
    def execute(
        self,
        log_text: Optional[str] = None,
        log_path: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> ReportOutput:
        """
        Ejecuta el caso de uso completo.
        
        Args:
            log_text: Texto de logs directamente (para API)
            log_path: Path al archivo de logs (para CLI)
            run_id: Identificador único de ejecución (se genera si no se provee)
        
        Returns:
            ReportOutput con paths generados y resumen
        
        Raises:
            ValueError: Si no se provee ni log_text ni log_path
            Exception: Si falla alguna etapa del proceso
        """
        # Generar run_id si no existe
        if run_id is None:
            run_id = self._generate_run_id()
        
        log_with_run_id(logger, logging.INFO, run_id, "Iniciando generación de reporte")
        
        # 1. Obtener texto de logs
        if log_text is None and log_path is None:
            raise ValueError("Debe proveer log_text o log_path")
        
        if log_text is None:
            log_with_run_id(
                logger, 
                logging.INFO, 
                run_id, 
                f"{Constants.LOG_READING_FILE}: {log_path}"
            )
            log_text = self.log_reader.read_log(log_path)
        
        log_with_run_id(
            logger, 
            logging.INFO, 
            run_id, 
            f"Log cargado: {len(log_text)} caracteres"
        )
        
        # 2. Analizar logs con analyzer determinista
        log_with_run_id(logger, logging.INFO, run_id, Constants.LOG_ANALYZING)
        analysis_dict = self.analyzer.analyze(log_text)
        analysis = LogAnalysis(**analysis_dict)
        
        log_with_run_id(
            logger, 
            logging.INFO, 
            run_id, 
            f"{Constants.LOG_ANALYSIS_COMPLETE}: "
            f"{analysis.summary['total_events']} eventos, "
            f"{analysis.summary['total_errors']} errores, "
            f"{analysis.summary['total_warnings']} warnings"
        )
        
        # 3. Construir prompt robusto para LLM
        prompt = self._build_llm_prompt(analysis_dict, log_text)
        
        # 4. Llamar a LLM para generar reporte (con cache si aplica)
        log_with_run_id(logger, logging.INFO, run_id, Constants.LOG_GENERATING_REPORT)
        report_markdown = self._get_or_generate_report(prompt, log_text, run_id)
        
        # 5. Escribir archivos de salida
        log_with_run_id(logger, logging.INFO, run_id, Constants.LOG_WRITING_OUTPUT)
        
        # Asegurar que existen los directorios
        settings.ensure_output_dirs()
        
        # Escribir análisis JSON
        analysis_path = self.report_writer.write_analysis(
            run_id=run_id,
            analysis=analysis_dict
        )
        
        # Escribir reporte(s) segun formato
        report_paths = self._write_reports(run_id, report_markdown, analysis_dict)
        
        log_with_run_id(
            logger, 
            logging.INFO, 
            run_id, 
            f"{Constants.LOG_REPORT_GENERATED}: {report_paths}"
        )
        
        # 6. Construir y retornar output
        output = ReportOutput(
            run_id=run_id,
            report_paths=report_paths,
            analysis_path=analysis_path,
            summary=analysis.summary,
            report_format=settings.REPORT_FORMAT
        )
        
        return output
    
    def _generate_run_id(self) -> str:
        """Genera un identificador único para la ejecución"""
        return uuid4().hex[:12]
    
    def _build_llm_prompt(self, analysis: dict, log_text: str) -> str:
        """
        Construye el prompt para el LLM incluyendo:
        - Análisis estructurado en JSON
        - Extracto de logs originales
        
        Args:
            analysis: Diccionario con el análisis estructurado
            log_text: Texto original de logs
        
        Returns:
            Prompt formateado para el LLM
        """
        # Serializar análisis a JSON limpio
        analysis_json = json.dumps(analysis, indent=2, ensure_ascii=False)
        
        # Extraer primeras líneas del log (extracto)
        log_lines = log_text.splitlines()
        excerpt_lines = min(30, len(log_lines))
        log_excerpt = "\n".join(log_lines[:excerpt_lines])
        if len(log_lines) > excerpt_lines:
            log_excerpt += f"\n... ({len(log_lines) - excerpt_lines} líneas adicionales)"
        
        # Construir prompt usando template
        prompt = Constants.LLM_USER_PROMPT_TEMPLATE.format(
            analysis_json=analysis_json,
            log_excerpt=log_excerpt
        )
        
        return prompt

    def _get_or_generate_report(
        self,
        prompt: str,
        log_text: str,
        run_id: str
    ) -> str:
        """
        Obtiene un reporte desde cache o genera uno nuevo.

        Args:
            prompt: Prompt para el LLM
            log_text: Texto de logs original
            run_id: Identificador de la ejecucion

        Returns:
            Reporte generado (Markdown)
        """
        if not settings.CACHE_ENABLED or self.cache is None:
            return self.llm.generate_text(
                prompt=prompt,
                system_prompt=Constants.LLM_SYSTEM_PROMPT
            )

        cache_key = build_cache_key(
            input_text=log_text,
            provider=settings.LLM_PROVIDER,
            model=self._resolve_model_name(),
            system_prompt=Constants.LLM_SYSTEM_PROMPT
        )

        cached = self.cache.get(cache_key)
        if cached is not None:
            log_with_run_id(logger, logging.INFO, run_id, Constants.LOG_CACHE_HIT)
            return cached

        log_with_run_id(logger, logging.INFO, run_id, Constants.LOG_CACHE_MISS)
        report = self.llm.generate_text(
            prompt=prompt,
            system_prompt=Constants.LLM_SYSTEM_PROMPT
        )
        self.cache.set(cache_key, report, ttl_seconds=settings.CACHE_TTL_SECONDS)
        return report

    def _resolve_model_name(self) -> str:
        """Resuelve el modelo activo segun el proveedor configurado."""
        if settings.LLM_PROVIDER == "ollama":
            return settings.OLLAMA_MODEL
        if settings.LLM_PROVIDER == "openai":
            return settings.OPENAI_MODEL
        if settings.LLM_PROVIDER == "anthropic":
            return settings.ANTHROPIC_MODEL
        if settings.LLM_PROVIDER == "google":
            return settings.GOOGLE_MODEL
        return "unknown"

    def _write_reports(self, run_id: str, report_markdown: str, analysis: dict) -> dict:
        """
        Escribe reportes segun el formato configurado.

        Args:
            run_id: Identificador de la ejecucion
            report_markdown: Reporte en Markdown
            analysis: Analisis estructurado

        Returns:
            Diccionario con paths por formato
        """
        report_paths = {}
        report_format = settings.REPORT_FORMAT

        if report_format in [Constants.REPORT_FORMAT_MARKDOWN, Constants.REPORT_FORMAT_BOTH]:
            report_paths[Constants.REPORT_FORMAT_MARKDOWN] = self.report_writer.write_report(
                run_id=run_id,
                report_content=report_markdown,
                report_format=Constants.REPORT_FORMAT_MARKDOWN,
                analysis=analysis
            )

        if report_format in [Constants.REPORT_FORMAT_EXCEL, Constants.REPORT_FORMAT_BOTH]:
            report_paths[Constants.REPORT_FORMAT_EXCEL] = self.report_writer.write_report(
                run_id=run_id,
                report_content=report_markdown,
                report_format=Constants.REPORT_FORMAT_EXCEL,
                analysis=analysis
            )

        return report_paths


class DownloadReportUseCase:
    """
    Caso de uso: Generar y descargar un reporte con múltiples archivos y formatos.
    
    Flujo:
    1. Validar entrada (nombre, formato, lista de archivos)
    2. Validar límite de archivos
    3. Validar que los archivos existen
    4. Leer y analizar todos los archivos
    5. Generar reporte en el formato solicitado
    6. Retornar artifact con path y metadatos para descarga
    """
    
    def __init__(
        self,
        log_reader: LogReaderPort,
        analyzer: AnalyzerPort,
        llm: LLMPort,
        report_writer: ReportWriterPort,
        cache: Optional[CachePort] = None,
        max_files: int = 10
    ):
        self.log_reader = log_reader
        self.analyzer = analyzer
        self.llm = llm
        self.report_writer = report_writer
        self.cache = cache
        self.max_files = max_files
        self.generate_case = GenerateReportUseCase(
            log_reader=log_reader,
            analyzer=analyzer,
            llm=llm,
            report_writer=report_writer,
            cache=cache
        )
    
    def execute(
        self,
        report_name: str,
        format_str: str,
        files: List[str],
        datasets_dir: str,
        run_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Ejecuta el caso de uso de descarga de reporte.
        
        Args:
            report_name: Nombre del reporte a generar
            format_str: Formato (excel, txt, csv, doc)
            files: Lista de nombres de archivos a incluir
            datasets_dir: Ruta al directorio con los datasets
            run_id: ID único para la ejecución (se genera si no existe)
        
        Returns:
            Dict con "path": str, "size_bytes": int, "format": str, "name": str
        
        Raises:
            ValueError: Si la validación falla
            FileNotFoundError: Si archivos no existen
            IOError: Si hay error de escritura
        """
        # Generar run_id si no existe
        if run_id is None:
            run_id = self._generate_run_id()
        
        logger.info(f"[{run_id}] Iniciando descarga de reporte: {report_name} ({format_str})")
        
        # 1. Validar entrada
        self._validate_request(report_name, format_str, files)
        
        # 2. Validar límite de archivos
        if len(files) > self.max_files:
            raise ValueError(
                f"Máximo {self.max_files} archivos permitidos, se solicitaron {len(files)}"
            )
        
        logger.info(f"[{run_id}] Validación exitosa: {len(files)} archivo(s)")
        
        # 3. Validar que los archivos existen
        from pathlib import Path
        for filename in files:
            file_path = Path(datasets_dir) / filename
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {filename}")
        
        # 4. Leer y analizar todos los archivos
        logger.info(f"[{run_id}] Leyendo {len(files)} archivo(s)...")
        combined_logs = self._read_and_combine_logs(files, datasets_dir)
        
        # 5. Generar reporte usando GenerateReportUseCase
        logger.info(f"[{run_id}] Generando reporte en formato: {format_str}")
        result = self.generate_case.execute(
            log_text=combined_logs,
            run_id=run_id
        )
        
        # 6. Obtener el archivo en el formato solicitado
        report_path = self._get_formatted_report(
            run_id=run_id,
            format_str=format_str,
            combined_logs=combined_logs,
            analysis=self._extract_analysis(result)
        )
        
        # 7. Obtener metadatos del archivo
        from pathlib import Path
        file_size = Path(report_path).stat().st_size
        
        logger.info(
            f"[{run_id}] Reporte generado exitosamente: "
            f"{report_path} ({file_size} bytes)"
        )
        
        return {
            "path": report_path,
            "size_bytes": file_size,
            "format": format_str,
            "name": report_name
        }
    
    def _validate_request(self, report_name: str, format_str: str, files: List[str]) -> None:
        """Valida que los parámetros de entrada sean válidos"""
        if not report_name or not report_name.strip():
            raise ValueError("El nombre del reporte no puede estar vacío")
        
        if not format_str or not format_str.strip():
            raise ValueError("El formato no puede estar vacío")
        
        # Validar que el formato es soportado
        supported = {"excel", "txt", "csv", "doc"}
        if format_str.lower() not in supported:
            raise ValueError(
                f"Formato no soportado: {format_str}. "
                f"Formatos válidos: {', '.join(supported)}"
            )
        
        if not files or len(files) == 0:
            raise ValueError("Debe especificar al menos un archivo")
    
    def _read_and_combine_logs(self, files: List[str], datasets_dir: str) -> str:
        """
        Lee múltiples archivos y los combina en un único texto.
        
        Args:
            files: Lista de nombres de archivos
            datasets_dir: Directorio donde están ubicados
        
        Returns:
            Todo el contenido combinado
        """
        combined = ""
        for filename in files:
            from pathlib import Path
            file_path = Path(datasets_dir) / filename
            content = self.log_reader.read_log(str(file_path))
            
            # Agregar separador entre archivos si hay más de uno
            if combined:
                combined += f"\n\n--- Archivo: {filename} ---\n\n"
            else:
                combined += f"--- Archivo: {filename} ---\n\n"
            
            combined += content
        
        return combined
    
    def _get_formatted_report(
        self,
        run_id: str,
        format_str: str,
        combined_logs: str,
        analysis: Dict
    ) -> str:
        """
        Escribe el reporte en el formato solicitado.
        
        Args:
            run_id: ID de ejecución
            format_str: Formato de salida
            combined_logs: Logs combinados del análisis
            analysis: Análisis estructurado
        
        Returns:
            Path del archivo generado
        """
        # Construir contenido del reporte en el formato nativo
        report_content = self._build_report_content(combined_logs, analysis)
        
        # Escribir en el formato solicitado
        return self.report_writer.write_report(
            run_id=run_id,
            report_content=report_content,
            report_format=format_str.lower(),
            analysis=analysis
        )
    
    def _build_report_content(self, log_text: str, analysis: Dict) -> str:
        """Construye el contenido del reporte a partir del log y análisis"""
        lines = [
            "# Reporte de Análisis de Logs",
            "",
            "## Resumen",
            ""
        ]
        
        if analysis and "summary" in analysis:
            for key, value in analysis["summary"].items():
                lines.append(f"- {key}: {value}")
        
        lines.extend([
            "",
            "## Detalles",
            ""
        ])
        
        if analysis and "error_groups" in analysis:
            lines.append("### Grupos de Errores")
            for group in analysis["error_groups"][:10]:  # Limitar a 10
                exception = group.get("exception", "Unknown")
                count = group.get("count", 0)
                lines.append(f"- {exception}: {count} ocurrencias")
        
        return "\n".join(lines)
    
    def _extract_analysis(self, report_output: ReportOutput) -> Dict:
        """Extrae el análisis del ReportOutput"""
        return {
            "summary": report_output.summary,
            "error_groups": [],  # Simplificado
            "warnings": []
        }
    
    def _generate_run_id(self) -> str:
        """Genera un identificador único para la ejecución"""
        return str(uuid4())[:8]
