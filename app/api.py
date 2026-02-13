"""
Entrypoint API (Flask) para AI Reporting Lab - Spec 1.
Expone endpoint REST para generación de reportes con Swagger UI.

ADVERTENCIA DE SEGURIDAD:
⚠️ Esta API NO tiene autenticación implementada.
⚠️ NO expongas esto en producción sin agregar autenticación/autorización.
⚠️ Riesgo de prompt injection si los logs contienen contenido malicioso.

Uso:
    python app/api.py
    
    # Swagger UI disponible en:
    http://localhost:8080/apidocs
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar src
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, request, jsonify, send_file, Response
from flasgger import Swagger, swag_from
import logging

from src.config.logging_config import setup_logging
from src.config.settings import settings
from src.config.constants import Constants
from src.domain.use_cases import GenerateReportUseCase, ListLogsUseCase, DownloadReportUseCase
from src.domain.analyze_use_case import AnalyzeLogUseCase
from src.domain.dtos import AnalyzeRequest, ErrorResponse
from src.domain.enums import OutputFormat
from src.domain.reporting.dtos import ReportRequest as ReportingRequest
from src.domain.reporting.use_case import GenerateReportUseCase as ReportingGenerateReportUseCase
from src.domain.reporting.enums import ReportFormat
from src.domain.reporting.exceptions import (
    ReportingError,
    InvalidFormatError,
    ValidationError,
    ReportGenerationError,
    LLMProviderError,
)
from src.domain.code_quality.dtos import CodeQualityReportRequest
from src.domain.code_quality.use_case import GenerateCodeQualityReportUseCase
from src.adapters.log_reader_fs import FileSystemLogReader
from src.domain.log_analyzer.analyzer import LogAnalyzer
from src.adapters.llm_factory import create_llm
from src.adapters.cache_memory import MemoryCache
from src.adapters.report_writer_fs import FileSystemReportWriter
from src.adapters.report_writer_factory import get_writer


# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Crear app Flask
app = Flask(__name__)

# Configurar Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "LLM Reporting Core API - AI Reporting Lab Spec 1",
        "description": "API REST para generación de reportes con análisis determinístico y narrativa LLM opcional. Arquitectura hexagonal - Módulo base únicamente.",
        "version": "1.0.0",
        "contact": {
            "name": "AI Reporting Lab",
            "url": "https://github.com/log-analyzer"
        }
    },
    "host": "localhost:8080",
    "basePath": "/",
    "schemes": ["http"],
    "securityDefinitions": {
        "APIKeyHeader": {
            "type": "apiKey",
            "name": "X-API-Key",
            "in": "header",
            "description": "API Key (no implementado aún)"
        }
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Componer dependencias (singleton para la app)
log_reader = FileSystemLogReader()
analyzer = LogAnalyzer()
llm = create_llm()
cache = MemoryCache()
report_writer = FileSystemReportWriter()

use_case = GenerateReportUseCase(
    log_reader=log_reader,
    analyzer=analyzer,
    llm=llm,
    report_writer=report_writer,
    cache=cache
)

list_logs_use_case = ListLogsUseCase(
    log_reader=log_reader
)

download_report_use_case = DownloadReportUseCase(
    log_reader=log_reader,
    analyzer=analyzer,
    llm=llm,
    report_writer=report_writer,
    cache=cache,
    max_files=settings.REPORT_DOWNLOAD_MAX_FILES
)

reporting_use_case = ReportingGenerateReportUseCase(llm=llm)

analyze_use_case = AnalyzeLogUseCase(
    log_reader=log_reader,
    analyzer=analyzer,
    llm=llm,
    cache=cache
)

# Code Quality use case
code_quality_use_case = GenerateCodeQualityReportUseCase(llm=llm)


# =========================================================================
# DOCUMENTACIÓN SWAGGER PROFESIONAL
# =========================================================================

DOWNLOAD_REPORT_SWAGGER_SPEC = {
    "tags": ["Reports"],
    "summary": "Genera y descarga un reporte en el formato especificado",
    "description": """
Endpoint principal del Spec 1 - AI Reporting Lab.

Genera un reporte con análisis determinístico y narrativa LLM opcional.
El reporte se retorna como archivo descargable (attachment) sin guardarse permanentemente.

**Formatos soportados:**
- `excel` - Archivo Excel (.xlsx) con tablas formateadas
- `csv` - Archivo CSV con datos tabulares
- `txt` - Archivo de texto plano
- `markdown` - Archivo Markdown (.md)
- `doc` - Archivo Word (.docx)

**Arquitectura:**
- Módulo: Spec 1 (base)
- Patrón: Arquitectura hexagonal
- Output: Bytes en memoria (no persiste en carpeta)
- Validación: Schema cerrado, sin propiedades adicionales

**Ejemplo de uso:**
```bash
curl -X POST http://localhost:8080/reports/download \\
  -H "Content-Type: application/json" \\
  -d '{
    "report_name": "audit_001",
    "format": "excel",
    "input_text": "sample text to analyze",
    "run_id": "run-001",
    "llm_enabled": true,
    "context": {
      "tool": "generic",
      "environment": "production"
    }
  }' --output report.xlsx
```
""",
    "consumes": ["application/json"],
    "produces": ["application/octet-stream"],
    "parameters": [
        {
            "in": "body",
            "name": "body",
            "description": "Payload para generar el reporte",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["report_name", "format", "input_text", "llm_enabled", "context"],
                "additionalProperties": False,
                "properties": {
                    "report_name": {
                        "type": "string",
                        "description": "Nombre identificador del reporte",
                        "example": "audit_001",
                        "minLength": 1
                    },
                    "format": {
                        "type": "string",
                        "description": "Formato de exportación del reporte",
                        "enum": ["excel", "csv", "txt", "markdown", "doc"],
                        "example": "excel"
                    },
                    "input_text": {
                        "type": "string",
                        "description": "Texto de entrada a analizar",
                        "example": "sample text to analyze",
                        "minLength": 1
                    },
                    "run_id": {
                        "type": "string",
                        "description": "ID de ejecución opcional (se genera automáticamente si no se provee)",
                        "example": "run-001"
                    },
                    "llm_enabled": {
                        "type": "boolean",
                        "description": "Habilitar generación de narrativa con LLM",
                        "example": True
                    },
                    "context": {
                        "type": "object",
                        "description": "Contexto adicional para el análisis (objeto cerrado)",
                        "required": ["tool"],
                        "additionalProperties": False,
                        "properties": {
                            "tool": {
                                "type": "string",
                                "description": "Herramienta que genera el reporte",
                                "example": "generic"
                            },
                            "environment": {
                                "type": "string",
                                "description": "Entorno de ejecución opcional",
                                "example": "production"
                            }
                        },
                        "example": {
                            "tool": "generic",
                            "environment": "production"
                        }
                    }
                },
                "example": {
                    "report_name": "audit_001",
                    "format": "excel",
                    "input_text": "sample text to analyze",
                    "run_id": "run-001",
                    "llm_enabled": True,
                    "context": {
                        "tool": "generic",
                        "environment": "production"
                    }
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "Archivo binario del reporte generado (attachment)",
            "headers": {
                "Content-Disposition": {
                    "description": "Nombre del archivo adjunto",
                    "type": "string",
                    "example": "attachment; filename=\"audit_001.xlsx\""
                },
                "X-Run-Id": {
                    "description": "ID de ejecución del reporte",
                    "type": "string",
                    "example": "run-001"
                }
            },
            "schema": {
                "type": "string",
                "format": "binary",
                "description": "Contenido binario del archivo (Excel, CSV, TXT, Markdown o DOC)"
            }
        },
        400: {
            "description": "Error de validación en la solicitud",
            "schema": {
                "type": "object",
                "required": ["status", "error_code", "message", "run_id"],
                "additionalProperties": False,
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["error"],
                        "example": "error"
                    },
                    "error_code": {
                        "type": "string",
                        "example": "VALIDATION_ERROR",
                        "description": "Código de error: VALIDATION_ERROR"
                    },
                    "message": {
                        "type": "string",
                        "example": "Missing required field: input_text"
                    },
                    "run_id": {
                        "type": "string",
                        "example": "run-123"
                    }
                }
            },
            "examples": {
                "application/json": {
                    "status": "error",
                    "error_code": "VALIDATION_ERROR",
                    "message": "Missing required field: input_text",
                    "run_id": "run-123"
                }
            }
        },
        422: {
            "description": "Formato no soportado o parámetros inválidos",
            "schema": {
                "type": "object",
                "required": ["status", "error_code", "message", "run_id"],
                "additionalProperties": False,
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["error"],
                        "example": "error"
                    },
                    "error_code": {
                        "type": "string",
                        "example": "INVALID_FORMAT",
                        "description": "Código de error: INVALID_FORMAT"
                    },
                    "message": {
                        "type": "string",
                        "example": "Format not supported"
                    },
                    "run_id": {
                        "type": "string",
                        "example": "run-124"
                    }
                }
            },
            "examples": {
                "application/json": {
                    "status": "error",
                    "error_code": "INVALID_FORMAT",
                    "message": "Format not supported: pdf",
                    "run_id": "run-124"
                }
            }
        },
        500: {
            "description": "Error interno del servidor o proveedor LLM",
            "schema": {
                "type": "object",
                "required": ["status", "error_code", "message", "run_id"],
                "additionalProperties": False,
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["error"],
                        "example": "error"
                    },
                    "error_code": {
                        "type": "string",
                        "example": "REPORT_GENERATION_ERROR",
                        "description": "Códigos: REPORT_GENERATION_ERROR, LLM_PROVIDER_ERROR, REPORTING_ERROR"
                    },
                    "message": {
                        "type": "string",
                        "example": "Failed to generate report"
                    },
                    "run_id": {
                        "type": "string",
                        "example": "run-125"
                    }
                }
            },
            "examples": {
                "application/json": {
                    "status": "error",
                    "error_code": "REPORT_GENERATION_ERROR",
                    "message": "Failed to generate report",
                    "run_id": "run-125"
                }
            }
        }
    }
}

CODE_QUALITY_REPORT_SWAGGER_SPEC = {
    "tags": ["CodeQuality"],
    "summary": "Analiza calidad de código y genera reporte descargable",
    "description": """
Feature: Code Quality Audit - Multi-tecnología

Analiza proyectos locales (Spring Boot, Angular, Python) y genera reportes de calidad de código.

**Tecnologías soportadas:**
- `Spring Boot` - Detecta pom.xml/build.gradle + src/main/java
- `Angular` - Detecta package.json + angular.json
- `Python` - Detecta requirements.txt/pyproject.toml + archivos .py

**Métricas generales:**
- Total de archivos
- Total de líneas
- Promedio de líneas por archivo

**Métricas específicas por tecnología:**

*Spring Boot:*
- Número de clases
- Número de @RestController
- Número de @Service
- Número de @Repository

*Angular:*
- Número de componentes (.component.ts)
- Número de services (.service.ts)
- Estimación de bundle size

*Python:*
- Número de módulos
- Número de funciones
- Número de clases

**Ejemplo de uso:**
```bash
curl -X POST http://localhost:8080/code-quality/reports/download \\
  -H "Content-Type: application/json" \\
  -d '{
    "report_name": "quality_001",
    "format": "excel",
    "project_path": "/path/to/project",
    "llm_enabled": true,
    "context": {
      "tech": "auto"
    }
  }' --output quality_report.xlsx
```
""",
    "consumes": ["application/json"],
    "produces": ["application/octet-stream"],
    "parameters": [
        {
            "in": "body",
            "name": "body",
            "description": "Payload para análisis de calidad de código",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["report_name", "format", "project_path"],
                "additionalProperties": False,
                "properties": {
                    "report_name": {
                        "type": "string",
                        "description": "Nombre del reporte de calidad",
                        "example": "quality_001",
                        "minLength": 1
                    },
                    "format": {
                        "type": "string",
                        "description": "Formato de exportación",
                        "enum": ["excel", "csv", "txt", "markdown", "doc"],
                        "example": "excel"
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Ruta absoluta al proyecto a analizar",
                        "example": "C:/projects/my-spring-app",
                        "minLength": 1
                    },
                    "run_id": {
                        "type": "string",
                        "description": "ID de ejecución opcional",
                        "example": "run-quality-001"
                    },
                    "llm_enabled": {
                        "type": "boolean",
                        "description": "Generar narrativa técnica con LLM",
                        "example": True
                    },
                    "language": {
                        "type": "string",
                        "description": "Idioma para la narrativa LLM (solo afecta narrativa, no métricas)",
                        "enum": ["es-AR", "es", "en"],
                        "default": "es-AR",
                        "example": "es-AR"
                    },
                    "include_globs": {
                        "type": "array",
                        "description": "Patrones de archivos a incluir (opcional)",
                        "items": {
                            "type": "string"
                        },
                        "example": ["**/*.java", "**/*.ts"]
                    },
                    "exclude_globs": {
                        "type": "array",
                        "description": "Patrones de archivos a excluir",
                        "items": {
                            "type": "string"
                        },
                        "example": ["**/target/**", "**/node_modules/**"]
                    },
                    "context": {
                        "type": "object",
                        "description": "Contexto del análisis (objeto cerrado)",
                        "additionalProperties": False,
                        "properties": {
                            "tech": {
                                "type": "string",
                                "description": "Tecnología (auto detecta si es 'auto')",
                                "example": "auto"
                            }
                        }
                    }
                },
                "example": {
                    "report_name": "quality_001",
                    "format": "excel",
                    "project_path": "C:/projects/my-app",
                    "run_id": "run-quality-001",
                    "llm_enabled": True,
                    "language": "es-AR",
                    "include_globs": [],
                    "exclude_globs": ["**/target/**", "**/node_modules/**"],
                    "context": {
                        "tech": "auto"
                    }
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "Reporte de calidad generado (attachment)",
            "headers": {
                "Content-Disposition": {
                    "description": "Nombre del archivo",
                    "type": "string",
                    "example": "attachment; filename=\"quality_001.xlsx\""
                },
                "X-Run-Id": {
                    "description": "ID de ejecución",
                    "type": "string",
                    "example": "run-quality-001"
                }
            },
            "schema": {
                "type": "string",
                "format": "binary"
            }
        },
        400: {
            "description": "Error de validación o tecnología no detectada",
            "schema": {
                "type": "object",
                "required": ["status", "error_code", "message", "run_id"],
                "additionalProperties": False,
                "properties": {
                    "status": {"type": "string", "enum": ["error"]},
                    "error_code": {"type": "string", "example": "VALIDATION_ERROR"},
                    "message": {"type": "string", "example": "Project path does not exist"},
                    "run_id": {"type": "string", "example": "run-123"}
                }
            }
        },
        422: {
            "description": "Formato no soportado",
            "schema": {
                "type": "object",
                "required": ["status", "error_code", "message", "run_id"],
                "additionalProperties": False,
                "properties": {
                    "status": {"type": "string", "enum": ["error"]},
                    "error_code": {"type": "string", "example": "INVALID_FORMAT"},
                    "message": {"type": "string"},
                    "run_id": {"type": "string"}
                }
            }
        },
        500: {
            "description": "Error durante análisis o generación",
            "schema": {
                "type": "object",
                "required": ["status", "error_code", "message", "run_id"],
                "additionalProperties": False,
                "properties": {
                    "status": {"type": "string", "enum": ["error"]},
                    "error_code": {"type": "string", "example": "REPORT_GENERATION_ERROR"},
                    "message": {"type": "string"},
                    "run_id": {"type": "string"}
                }
            }
        }
    }
}


# =========================================================================
# ENDPOINTS
# =========================================================================

@app.route("/", methods=["GET"])
def index():
    """
    Información de la API
    ---
    tags:
      - Info
    responses:
      200:
        description: Información del servicio
        schema:
          type: object
          additionalProperties: false
          properties:
            service:
              type: string
              example: AI Reporting Lab - Spec 1
            version:
              type: string
              example: 1.0.0
            swagger_ui:
              type: string
              example: http://localhost:8080/apidocs
    """
    return jsonify({
        "service": "AI Reporting Lab - Spec 1",
        "version": "1.0.0",
        "swagger_ui": "http://localhost:8080/apidocs",
        "endpoints": {
            "/": "GET - Info de la API",
            "/health": "GET - Health check",
            "/reports/download": "POST - Descarga reporte en formato especificado"
        }
    })


@app.route("/health", methods=["GET"])
def health():
    """
    Health check
    ---
    tags:
      - Info
    responses:
      200:
        description: Servicio saludable
        schema:
          type: object
          additionalProperties: false
          properties:
            status:
              type: string
              example: healthy
    """
    return jsonify({
        "status": "healthy"
    }), 200


@app.route("/reports/download", methods=["POST"])
@swag_from(DOWNLOAD_REPORT_SWAGGER_SPEC)
def download_report():
    """Endpoint principal para generar y descargar reportes (Spec 1)."""
    
    # Validar Content-Type
    if not request.is_json:
        raise ValidationError("Content-Type must be application/json")

    # Parsear y validar request
    data = request.get_json() or {}
    report_request = ReportingRequest.from_dict(data)

    logger.info(f"[{report_request.run_id}] Generando reporte: {report_request.report_name} ({report_request.format.value})")

    # Ejecutar caso de uso
    result = reporting_use_case.execute(report_request)
    payload = reporting_use_case.to_writer_payload(result)
    
    # Obtener writer según formato
    writer = get_writer(result.format)

    # Generar contenido en bytes
    try:
        content = writer.write(payload)
    except Exception as exc:
        logger.error(f"[{report_request.run_id}] Error al escribir reporte: {exc}")
        raise ReportGenerationError(str(exc), run_id=report_request.run_id)

    # Mapeo de formatos a MIME types
    format_mime = {
        ReportFormat.EXCEL: Constants.MIME_TYPE_EXCEL,
        ReportFormat.CSV: Constants.MIME_TYPE_CSV,
        ReportFormat.TXT: Constants.MIME_TYPE_TXT,
        ReportFormat.MARKDOWN: "text/markdown",
        ReportFormat.DOC: Constants.MIME_TYPE_DOC,
    }

    # Mapeo de formatos a extensiones
    format_ext = {
        ReportFormat.EXCEL: ".xlsx",
        ReportFormat.CSV: ".csv",
        ReportFormat.TXT: ".txt",
        ReportFormat.MARKDOWN: ".md",
        ReportFormat.DOC: ".docx",
    }

    filename = f"{report_request.report_name}{format_ext[result.format]}"
    
    logger.info(f"[{report_request.run_id}] Reporte generado exitosamente: {filename}")

    # Crear respuesta con headers apropiados
    response = Response(content, mimetype=format_mime[result.format])
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["X-Run-Id"] = report_request.run_id
    
    return response


@app.route("/code-quality/reports/download", methods=["POST"])
@swag_from(CODE_QUALITY_REPORT_SWAGGER_SPEC)
def download_code_quality_report():
    """Endpoint para análisis de calidad de código y descarga de reporte."""
    
    # Validar Content-Type
    if not request.is_json:
        raise ValidationError("Content-Type must be application/json")
    
    # Parsear y validar request
    data = request.get_json() or {}
    quality_request = CodeQualityReportRequest.from_dict(data)
    
    logger.info(
        f"[{quality_request.run_id}] Starting code quality analysis: "
        f"{quality_request.report_name} @ {quality_request.project_path}"
    )
    
    # Ejecutar caso de uso
    result = code_quality_use_case.execute(quality_request)
    payload = code_quality_use_case.to_writer_payload(result)
    
    # Obtener writer según formato
    writer = get_writer(result.format)
    
    # Generar contenido en bytes
    try:
        content = writer.write(payload)
    except Exception as exc:
        logger.error(f"[{quality_request.run_id}] Error writing report: {exc}")
        raise ReportGenerationError(str(exc), run_id=quality_request.run_id)
    
    # Mapeo de formatos
    format_mime = {
        ReportFormat.EXCEL: Constants.MIME_TYPE_EXCEL,
        ReportFormat.CSV: Constants.MIME_TYPE_CSV,
        ReportFormat.TXT: Constants.MIME_TYPE_TXT,
        ReportFormat.MARKDOWN: "text/markdown",
        ReportFormat.DOC: Constants.MIME_TYPE_DOC,
    }
    
    format_ext = {
        ReportFormat.EXCEL: ".xlsx",
        ReportFormat.CSV: ".csv",
        ReportFormat.TXT: ".txt",
        ReportFormat.MARKDOWN: ".md",
        ReportFormat.DOC: ".docx",
    }
    
    filename = f"{quality_request.report_name}{format_ext[result.format]}"
    
    logger.info(f"[{quality_request.run_id}] Code quality report generated: {filename}")
    
    # Crear respuesta
    response = Response(content, mimetype=format_mime[result.format])
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["X-Run-Id"] = quality_request.run_id
    
    return response


# =========================================================================
# ERROR HANDLERS GLOBALES
# =========================================================================

@app.errorhandler(ReportingError)
def handle_reporting_error(error: ReportingError):
    """Handler global para errores del dominio reporting."""
    
    # Mapear tipo de error a status code HTTP
    status_code = 500
    if isinstance(error, ValidationError):
        status_code = 400
    elif isinstance(error, InvalidFormatError):
        status_code = 422
    elif isinstance(error, LLMProviderError):
        status_code = 500
    elif isinstance(error, ReportGenerationError):
        status_code = 500
    
    logger.error(f"[{error.run_id}] {error.error_code}: {error.message}")

    return jsonify({
        "status": "error",
        "error_code": error.error_code,
        "message": error.message,
        "run_id": error.run_id or "unknown"
    }), status_code


@app.errorhandler(Exception)
def handle_generic_error(error: Exception):
    """Handler global para errores no controlados."""
    logger.error(f"Unhandled error: {error}", exc_info=True)
    
    return jsonify({
        "status": "error",
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": str(error),
        "run_id": "unknown"
    }), 500


# =========================================================================
# APPLICATION FACTORY
# =========================================================================

def create_app():
    """Factory function para crear la aplicación Flask (útil para testing)."""
    return app


def main():
    """Inicia el servidor Flask."""
    import sys
    import io
    
    # Configurar encoding UTF-8 para stdout en Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 70)
    print("  AI Reporting Lab - Spec 1")
    print("  LLM Reporting Core API")
    print("=" * 70)
    print()
    print("  Arquitectura: Hexagonal")
    print("  Módulo: Base (Spec 1)")
    print()
    print(f"  LLM Provider: {settings.LLM_PROVIDER}")
    if settings.LLM_PROVIDER == "ollama":
        print(f"  Ollama URL: {settings.OLLAMA_BASE_URL}")
        print(f"  Modelo: {settings.OLLAMA_MODEL}")
    print()
    print("  WARNING: Esta API no tiene autenticacion.")
    print("  WARNING: No exponer en produccion sin seguridad.")
    print()
    print("=" * 70)
    print()
    print("Endpoints disponibles:")
    print("  GET  /              - Info de la API")
    print("  GET  /health        - Health check")
    print("  POST /reports/download - Generar y descargar reporte")
    print()
    print("Swagger UI: http://localhost:8080/apidocs")
    print("Iniciando servidor en http://0.0.0.0:8080")
    print()
    
    # Iniciar servidor
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False
    )


if __name__ == "__main__":
    main()
