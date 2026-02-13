"""
Caso de uso: Anรกlisis de logs con formato configurable.
Orquesta el proceso completo: carga, anรกlisis, generaciรณn de reporte y exportaciรณn.
"""

import logging
from pathlib import Path
from typing import Optional, Dict

from .dtos import AnalyzeRequest, AnalyzeResponse
from .enums import OutputFormat
from ..ports.log_reader_port import LogReaderPort
from ..ports.analyzer_port import AnalyzerPort
from ..ports.llm_port import LLMPort
from ..ports.cache_port import CachePort
from ..config.settings import settings
from ..config.constants import Constants
from ..config.logging_config import log_with_run_id
from ..adapters.cache_key import build_cache_key


logger = logging.getLogger(__name__)


class AnalyzeLogUseCase:
    """
    Caso de uso principal para analizar logs con formato de salida configurable.
    
    Flujo:
    1. Validar request
    2. Cargar log (desde texto o archivo)
    3. Analizar con regex (determinista)
    4. Generar reporte con LLM (Ollama)
    5. Exportar al formato solicitado
    6. Retornar response estructurado
    """
    
    def __init__(
        self,
        log_reader: LogReaderPort,
        analyzer: AnalyzerPort,
        llm: LLMPort,
        cache: Optional[CachePort] = None
    ):
        """
        Inicializa el caso de uso con sus dependencias.
        
        Args:
            log_reader: Puerto para leer logs
            analyzer: Puerto para analizar logs
            llm: Puerto para generar reportes con LLM
            cache: Puerto para cachear resultados (opcional)
        """
        self.log_reader = log_reader
        self.analyzer = analyzer
        self.llm = llm
        self.cache = cache
    
    def execute(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """
        Ejecuta el anรกlisis completo de logs.
        
        Args:
            request: Solicitud con parรกmetros validados
        
        Returns:
            Respuesta con path del archivo generado y resumen
        
        Raises:
            FileNotFoundError: Si el archivo de log no existe
            ConnectionError: Si no se puede conectar al LLM
            TimeoutError: Si el LLM excede el timeout
            Exception: Otros errores inesperados
        """
        run_id = request.run_id
        
        log_with_run_id(logger, logging.INFO, run_id, "Iniciando anรกlisis de logs")
        
        try:
            # 1. Cargar texto del log
            log_text = self._load_log_text(request, run_id)
            
            log_with_run_id(
                logger,
                logging.INFO,
                run_id,
                f"Log cargado: {len(log_text)} caracteres"
            )
            
            # 2. Analizar con regex (determinista)
            log_with_run_id(logger, logging.INFO, run_id, "Analizando estructura del log")
            analysis_dict = self.analyzer.analyze(log_text)
            
            log_with_run_id(
                logger,
                logging.INFO,
                run_id,
                f"Anรกlisis completado: {analysis_dict['summary']['total_events']} eventos, "
                f"{analysis_dict['summary']['total_errors']} errores"
            )
            
            # 3. Generar reporte con LLM
            log_with_run_id(logger, logging.INFO, run_id, "Generando reporte con LLM")
            report_content = self._generate_report_with_llm(log_text, analysis_dict, run_id)
            
            # 4. Preparar estructura de reporte
            report_data = self._prepare_report_data(report_content, analysis_dict)
            
            # 5. Exportar al formato solicitado
            log_with_run_id(
                logger,
                logging.INFO,
                run_id,
                f"Exportando reporte en formato: {request.output_format.value}"
            )
            
            output_path = self._export_report(
                run_id=run_id,
                output_filename=request.output_filename,
                output_format=request.output_format,
                report_data=report_data,
                analysis=analysis_dict
            )
            
            log_with_run_id(
                logger,
                logging.INFO,
                run_id,
                f"Reporte generado exitosamente: {output_path}"
            )
            
            # 6. Construir respuesta exitosa
            return AnalyzeResponse.success(
                run_id=run_id,
                output_path=output_path,
                output_format=request.output_format.value,
                summary=analysis_dict.get('summary', {})
            )
        
        except FileNotFoundError as e:
            log_with_run_id(logger, logging.ERROR, run_id, f"Archivo no encontrado: {e}")
            return AnalyzeResponse.error(run_id=run_id, error_message=str(e))
        
        except ConnectionError as e:
            log_with_run_id(logger, logging.ERROR, run_id, f"Error de conexiรณn: {e}")
            return AnalyzeResponse.error(run_id=run_id, error_message=str(e))
        
        except TimeoutError as e:
            log_with_run_id(logger, logging.ERROR, run_id, f"Timeout: {e}")
            return AnalyzeResponse.error(run_id=run_id, error_message=str(e))
        
        except Exception as e:
            log_with_run_id(logger, logging.ERROR, run_id, f"Error inesperado: {e}")
            logger.exception("Stacktrace completo:")
            return AnalyzeResponse.error(
                run_id=run_id,
                error_message=f"Error interno del servidor: {str(e)}"
            )
    
    def _load_log_text(self, request: AnalyzeRequest, run_id: str) -> str:
        """
        Carga el texto del log desde archivo.
        
        Args:
            request: Solicitud con input_log_filename
            run_id: ID de ejecución para logging
        
        Returns:
            Texto del log
        
        Raises:
            FileNotFoundError: Si el archivo no existe
        """
        # Leer desde archivo en datasets/
        log_path = settings.DATASETS_DIR / request.input_log_filename
        
        if not log_path.exists():
            raise FileNotFoundError(
                f"Archivo '{request.input_log_filename}' no existe en {settings.DATASETS_DIR}"
            )
        
        log_with_run_id(
            logger,
            logging.INFO,
            run_id,
            f"Leyendo log desde archivo: {log_path}"
        )
        
        return self.log_reader.read_log(str(log_path))
    
    def _generate_report_with_llm(
        self,
        log_text: str,
        analysis: Dict,
        run_id: str
    ) -> str:
        """
        Genera el reporte usando LLM (con cache si estรก habilitado).
        
        Args:
            log_text: Texto original del log
            analysis: Anรกlisis estructurado
            run_id: ID de ejecuciรณn
        
        Returns:
            Reporte generado en Markdown
        """
        # Construir prompt para el LLM
        prompt = self._build_llm_prompt(analysis, log_text)
        
        # Usar cache si estรก habilitado
        if settings.CACHE_ENABLED and self.cache is not None:
            cache_key = build_cache_key(
                input_text=log_text,
                provider=settings.LLM_PROVIDER,
                model=self._resolve_model_name(),
                system_prompt=Constants.LLM_SYSTEM_PROMPT
            )
            
            cached = self.cache.get(cache_key)
            if cached is not None:
                log_with_run_id(logger, logging.INFO, run_id, "Cache hit")
                return cached
            
            log_with_run_id(logger, logging.INFO, run_id, "Cache miss")
        
        # Generar con LLM
        report = self.llm.generate_text(
            prompt=prompt,
            system_prompt=Constants.LLM_SYSTEM_PROMPT
        )
        
        # Guardar en cache si estรก habilitado
        if settings.CACHE_ENABLED and self.cache is not None:
            self.cache.set(cache_key, report, ttl_seconds=settings.CACHE_TTL_SECONDS)
        
        return report
    
    def _build_llm_prompt(self, analysis: Dict, log_text: str) -> str:
        """
        Construye el prompt para el LLM.
        
        Args:
            analysis: Anรกlisis estructurado
            log_text: Texto original del log
        
        Returns:
            Prompt formateado
        """
        import json
        
        # Serializar anรกlisis a JSON
        analysis_json = json.dumps(analysis, indent=2, ensure_ascii=False)
        
        # Extraer extracto del log
        log_lines = log_text.splitlines()
        excerpt_lines = min(30, len(log_lines))
        log_excerpt = "\n".join(log_lines[:excerpt_lines])
        if len(log_lines) > excerpt_lines:
            log_excerpt += f"\n... ({len(log_lines) - excerpt_lines} lรญneas adicionales)"
        
        # Construir prompt
        prompt = Constants.LLM_USER_PROMPT_TEMPLATE.format(
            analysis_json=analysis_json,
            log_excerpt=log_excerpt
        )
        
        return prompt
    
    def _prepare_report_data(self, report_content: str, analysis: Dict) -> Dict:
        """
        Prepara la estructura de datos del reporte para exportaciรณn.
        
        Args:
            report_content: Contenido del reporte en Markdown
            analysis: Anรกlisis estructurado
        
        Returns:
            Diccionario con toda la informaciรณn del reporte
        """
        return {
            'content': report_content,
            'analysis': analysis
        }
    
    def _export_report(
        self,
        run_id: str,
        output_filename: str,
        output_format: OutputFormat,
        report_data: Dict,
        analysis: Dict
    ) -> str:
        """
        Exporta el reporte al formato solicitado.
        
        Args:
            run_id: ID de ejecuciรณn
            output_filename: Nombre del archivo de salida (sin extensiรณn)
            output_format: Formato de salida
            report_data: Datos del reporte
            analysis: Anรกlisis estructurado
        
        Returns:
            Path absoluto del archivo generado
        """
        # Asegurar que existe el directorio de salida
        output_dir = settings.OUT_DIR / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Seleccionar el exporter apropiado e invocar
        from ..adapters.report_exporter_factory import ReportExporterFactory
        
        exporter = ReportExporterFactory.create(output_format)
        
        output_path = exporter.export(
            output_dir=str(output_dir),
            output_filename=output_filename,
            report_content=report_data['content'],
            analysis=analysis
        )
        
        return output_path
    
    def _resolve_model_name(self) -> str:
        """Resuelve el nombre del modelo segรบn el proveedor configurado"""
        if settings.LLM_PROVIDER == "ollama":
            return settings.OLLAMA_MODEL
        if settings.LLM_PROVIDER == "openai":
            return settings.OPENAI_MODEL
        if settings.LLM_PROVIDER == "anthropic":
            return settings.ANTHROPIC_MODEL
        if settings.LLM_PROVIDER == "google":
            return settings.GOOGLE_MODEL
        return "unknown"
