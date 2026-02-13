"""
Constantes del proyecto log_analyzer.
Centraliza strings, nombres de carpetas y labels compartidos.
"""


class Constants:
    """Constantes globales del proyecto"""
    
    # Carpetas de salida
    OUT_DIR_NAME = "out"
    REPORTS_DIR_NAME = "reports"
    ANALYSIS_DIR_NAME = "analysis"
    
    # Extensiones y formatos
    REPORT_FILE_EXTENSION = ".md"
    REPORT_FILE_EXTENSION_XLSX = ".xlsx"
    ANALYSIS_FILE_EXTENSION = ".json"

    REPORT_FORMAT_EXCEL = "excel"
    REPORT_FORMAT_MARKDOWN = "markdown"
    REPORT_FORMAT_BOTH = "both"
    REPORT_FORMAT_TXT = "txt"
    REPORT_FORMAT_CSV = "csv"
    REPORT_FORMAT_DOC = "doc"
    
    # MIME types para descarga
    MIME_TYPE_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    MIME_TYPE_TXT = "text/plain"
    MIME_TYPE_CSV = "text/csv"
    MIME_TYPE_DOC = "application/msword"
    
    # Default MIME type para formatos
    FORMAT_MIME_TYPES = {
        REPORT_FORMAT_EXCEL: MIME_TYPE_EXCEL,
        REPORT_FORMAT_TXT: MIME_TYPE_TXT,
        REPORT_FORMAT_CSV: MIME_TYPE_CSV,
        REPORT_FORMAT_DOC: MIME_TYPE_DOC,
    }
    
    # Extensiones de archivo por formato
    FORMAT_EXTENSIONS = {
        REPORT_FORMAT_EXCEL: REPORT_FILE_EXTENSION_XLSX,
        REPORT_FORMAT_TXT: ".txt",
        REPORT_FORMAT_CSV: ".csv",
        REPORT_FORMAT_DOC: ".doc",
    }
    
    # Nombres default
    DEFAULT_LOG_FILE = "generated_logs.txt"
    DEFAULT_DATASET_DIR = "datasets"
    
    # Labels de niveles de log
    LEVEL_ERROR = "ERROR"
    LEVEL_WARN = "WARN"
    LEVEL_INFO = "INFO"
    
    # Headers del reporte Markdown
    REPORT_TITLE = "📊 Reporte de Análisis de Logs"
    REPORT_EXECUTIVE_SUMMARY = "📈 Resumen Ejecutivo"
    REPORT_ERROR_TYPES = "🔴 Tipos de Errores Encontrados"
    REPORT_PATTERNS = "🔍 Análisis de Patrones"
    REPORT_ERROR_DETAILS = "📋 Detalle de Grupos de Errores"
    REPORT_WARNINGS = "⚡ Advertencias (WARN)"
    REPORT_FOOTER = "*Reporte generado automáticamente por Log Analyzer*"
    
    # Patterns para análisis
    PATTERN_REPEATED_ERRORS = "⚠️ Errores Repetitivos"
    PATTERN_HOTSPOTS = "🔥 Hotspots (Componentes más afectados)"
    PATTERN_TIMEFRAME = "⏱️ Ventana Temporal"
    
    # Límites de procesamiento
    MAX_WARNINGS_IN_ANALYSIS = 10
    MAX_EVENTS_IN_ANALYSIS = 50
    MAX_ERROR_GROUPS_IN_REPORT = 10
    MAX_HOTSPOTS = 5
    MAX_WARNING_SAMPLES = 5
    MAX_SAMPLES_PER_GROUP = 2
    
    # Prompts para LLM
    LLM_SYSTEM_PROMPT = """Eres un experto analista de logs y sistemas distribuidos.
Tu tarea es generar un reporte profesional en formato Markdown a partir del análisis estructurado de logs.
El reporte debe ser claro, técnico y orientado a desarrolladores/operadores."""
    
    LLM_USER_PROMPT_TEMPLATE = """Genera un reporte técnico profesional en formato Markdown basado en el siguiente análisis de logs.

ANÁLISIS ESTRUCTURADO (JSON):
```json
{analysis_json}
```

EXTRACTO DE LOGS (primeras líneas):
```
{log_excerpt}
```

REQUISITOS DEL REPORTE:
1. Título principal con emoji
2. Resumen ejecutivo con métricas clave
3. Análisis de patrones: errores repetitivos, hotspots, ventana temporal
4. Detalle de los grupos de errores más críticos (ordenados por frecuencia)
5. Tabla o listado de advertencias relevantes
6. Recomendaciones técnicas específicas basadas en los errores encontrados
7. Conclusión breve

Usa formato Markdown profesional con secciones, bullets, code blocks y énfasis apropiado.
"""
    
    # Mensajes de logging
    LOG_READING_FILE = "Leyendo logs desde archivo"
    LOG_ANALYZING = "Analizando estructura del log"
    LOG_ANALYSIS_COMPLETE = "Análisis completado"
    LOG_GENERATING_REPORT = "Generando reporte con LLM"
    LOG_REPORT_GENERATED = "Reporte generado exitosamente"
    LOG_CALLING_LLM = "Llamando a LLM para generar reporte"
    LOG_WRITING_OUTPUT = "Escribiendo archivos de salida"
    LOG_CACHE_HIT = "Cache hit"
    LOG_CACHE_MISS = "Cache miss"
    
    # Mensajes de error
    ERROR_FILE_NOT_FOUND = "No se encontró el archivo"
    ERROR_LLM_FAILED = "Error al llamar al LLM"
    ERROR_ANALYSIS_FAILED = "Error durante el análisis"
    ERROR_WRITE_FAILED = "Error al escribir archivo"
    
    # API
    API_ENDPOINT_ANALYZE = "/analyze"
    API_FIELD_LOG_TEXT = "log_text"
    API_FIELD_RUN_ID = "run_id"
    API_RESPONSE_STATUS = "status"
    API_RESPONSE_RUN_ID = "run_id"
    API_RESPONSE_REPORT_PATH = "report_path"
    API_RESPONSE_ANALYSIS_PATH = "analysis_path"
    API_RESPONSE_SUMMARY = "summary"
    API_RESPONSE_ERROR = "error"
    
    # Estados
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    
    # Security warnings
    SECURITY_WARNING_API = "⚠️ ADVERTENCIA: Esta API no tiene autenticación. No exponer en producción sin seguridad."
    SECURITY_WARNING_PROMPT_INJECTION = "⚠️ RIESGO: Posible prompt injection si los logs contienen instrucciones maliciosas."
