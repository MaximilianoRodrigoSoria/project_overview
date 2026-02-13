"""
Entrypoint API (Flask) para log_analyzer.
Expone endpoint REST para análisis de logs con Swagger UI.

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

from flask import Flask, request, jsonify, send_file
from flasgger import Swagger, swag_from
import logging

from src.config.logging_config import setup_logging
from src.config.settings import settings
from src.config.constants import Constants
from src.domain.use_cases import GenerateReportUseCase, ListLogsUseCase, DownloadReportUseCase
from src.domain.analyze_use_case import AnalyzeLogUseCase
from src.domain.dtos import AnalyzeRequest, ErrorResponse
from src.domain.enums import OutputFormat
from src.adapters.log_reader_fs import FileSystemLogReader
from src.domain.log_analyzer.analyzer import LogAnalyzer
from src.adapters.llm_factory import create_llm
from src.adapters.cache_memory import MemoryCache
from src.adapters.report_writer_fs import FileSystemReportWriter


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
        "title": "Log Analyzer API",
        "description": "API REST para análisis automático de logs con LLM (Ollama)",
        "version": "1.0.0",
        "contact": {
            "name": "Log Analyzer",
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

analyze_use_case = AnalyzeLogUseCase(
    log_reader=log_reader,
    analyzer=analyzer,
    llm=llm,
    cache=cache
)


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
          properties:
            service:
              type: string
              example: log_analyzer
            version:
              type: string
              example: 1.0.0
            swagger_ui:
              type: string
              example: http://localhost:8080/apidocs
    """
    return jsonify({
        "service": "log_analyzer",
        "version": "1.0.0",
        "swagger_ui": "http://localhost:8080/apidocs",
        "endpoints": {
            "/datasets": "GET - Lista archivos de logs disponibles",
            "/reports/download": "POST - Descarga reporte en formato (excel, txt, csv, doc)",
            "/analyze": "POST - Analiza logs y genera reporte"
        },
        "config": {
            "ollama_model": settings.OLLAMA_MODEL,
            "ollama_url": settings.OLLAMA_BASE_URL,
            "output_dir": str(settings.OUT_DIR),
            "datasets_dir": str(settings.DATASETS_DIR)
        }
    })


@app.route("/datasets", methods=["GET"])
def list_datasets():
    """
    Lista archivos de logs disponibles
    ---
    tags:
      - Datasets
    responses:
      200:
        description: Lista de archivos .txt en datasets/
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            files:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                    example: generated_logs.txt
                  size_bytes:
                    type: integer
                    example: 1024
                  path:
                    type: string
                    example: /absolute/path/to/generated_logs.txt
            count:
              type: integer
              example: 2
      404:
        description: Directorio de datasets no existe
      500:
        description: Error interno del servidor
    """
    try:
        # Usar el use case para listar logs
        result = list_logs_use_case.execute(str(settings.DATASETS_DIR))
        
        return jsonify({
            Constants.API_RESPONSE_STATUS: Constants.STATUS_SUCCESS,
            "files": result["files"],
            "count": result["count"]
        }), 200
        
    except FileNotFoundError as e:
        logger.error(f"Error al listar datasets: directorio no encontrado: {e}")
        return jsonify({
            Constants.API_RESPONSE_STATUS: Constants.STATUS_ERROR,
            Constants.API_RESPONSE_ERROR: "Directorio de datasets no existe"
        }), 404
        
    except Exception as e:
        logger.error(f"Error al listar datasets: {e}", exc_info=True)
        return jsonify({
            Constants.API_RESPONSE_STATUS: Constants.STATUS_ERROR,
            Constants.API_RESPONSE_ERROR: str(e)
        }), 500


@app.route(Constants.API_ENDPOINT_ANALYZE, methods=["POST"])
def analyze():
    """
    Analiza logs y descarga el reporte en formato configurable
    ---
    tags:
      - Análisis
    parameters:
      - in: body
        name: body
        required: true
        description: |
          Solicitud de análisis de logs con descarga automática.
          
          **Formatos disponibles:**
          - `excel` - Archivo Excel (.xlsx) con tablas formateadas
          - `csv` - Archivo CSV con datos tabulares
          - `txt` - Archivo de texto plano
          - `markdown` - Archivo Markdown con formato
          - `doc` - Archivo Word (.docx) - requiere python-docx instalado
        schema:
          type: object
          required:
            - input_log_filename
            - output_filename
            - output_format
          properties:
            input_log_filename:
              type: string
              description: Nombre del archivo de log en datasets/
              example: generated_logs.txt
            output_filename:
              type: string
              description: Nombre del archivo de salida (sin extensión)
              example: informe_produccion
            output_format:
              type: string
              description: Formato de salida del reporte
              enum: [excel, csv, txt, markdown, doc]
              example: excel
          example:
            input_log_filename: generated_logs.txt
            output_filename: informe_produccion
            output_format: excel
    responses:
      200:
        description: Descarga directa del archivo generado
        content:
          application/vnd.openxmlformats-officedocument.spreadsheetml.sheet:
            schema:
              type: string
              format: binary
          text/csv:
            schema:
              type: string
          application/msword:
            schema:
              type: string
              format: binary
          text/plain:
            schema:
              type: string
          text/markdown:
            schema:
              type: string
      400:
        description: Error de validación
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 400
            message:
              type: string
              example: Error de validación
            details:
              type: string
            run_id:
              type: string
              nullable: true
      404:
        description: Archivo de log no encontrado
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 404
            message:
              type: string
              example: Archivo no encontrado
            details:
              type: string
            run_id:
              type: string
      500:
        description: Error interno del servidor
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 500
            message:
              type: string
              example: Error interno del servidor
            details:
              type: string
            run_id:
              type: string
    """
    run_id = None
    
    try:
        # Validar Content-Type
        if not request.is_json:
            error = ErrorResponse(
                code=400,
                message="Content-Type debe ser application/json",
                details=None
            )
            return jsonify(error.to_dict()), 400
        
        # Obtener datos del request
        data = request.get_json()
        
        # Parsear y validar request usando DTO
        try:
            analyze_request = AnalyzeRequest.from_dict(data)
            run_id = analyze_request.run_id
        except ValueError as e:
            logger.error(f"Error de validación: {e}")
            error = ErrorResponse(
                code=400,
                message="Error de validación",
                details=str(e),
                run_id=run_id
            )
            return jsonify(error.to_dict()), 400
        
        logger.info(
            f"[{run_id}] Solicitud de análisis recibida: "
            f"input={analyze_request.input_log_filename}, "
            f"output={analyze_request.output_filename}.{analyze_request.output_format.value}"
        )
        
        # Ejecutar caso de uso
        response = analyze_use_case.execute(analyze_request)
        
        # Si la respuesta tiene status error, retornar el error apropiado
        if response.status == 'error':
            # Determinar código de error según el mensaje
            status_code = 500
            
            if "no encontrado" in response.errors.lower() or "no existe" in response.errors.lower():
                status_code = 404
            elif "timeout" in response.errors.lower():
                status_code = 504
            elif "conectar" in response.errors.lower():
                status_code = 503
            
            error = ErrorResponse(
                code=status_code,
                message=response.errors,
                details=None,
                run_id=run_id
            )
            return jsonify(error.to_dict()), status_code
        
        # Respuesta exitosa: descargar archivo
        logger.info(f"[{run_id}] Análisis completado exitosamente: {response.output_path}")
        
        # Determinar MIME type según formato
        mime_type = Constants.FORMAT_MIME_TYPES.get(
            response.output_format, 
            'application/octet-stream'
        )
        
        # Obtener extensión del archivo
        from pathlib import Path
        output_file = Path(response.output_path)
        download_name = f"{analyze_request.output_filename}{output_file.suffix}"
        
        # Enviar archivo para descarga
        return send_file(
            response.output_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=download_name
        )
        
    except ConnectionError as e:
        logger.error(f"[{run_id}] Error de conexión: {e}")
        error = ErrorResponse(
            code=503,
            message="No se puede conectar al proveedor LLM",
            details=str(e),
            run_id=run_id
        )
        return jsonify(error.to_dict()), 503
        
    except TimeoutError as e:
        logger.error(f"[{run_id}] Timeout: {e}")
        error = ErrorResponse(
            code=504,
            message="Timeout al procesar request",
            details=str(e),
            run_id=run_id
        )
        return jsonify(error.to_dict()), 504
        
    except Exception as e:
        logger.error(f"[{run_id}] Error inesperado: {e}", exc_info=True)
        error = ErrorResponse(
            code=500,
            message="Error interno del servidor",
            details=str(e),
            run_id=run_id
        )
        return jsonify(error.to_dict()), 500


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
          properties:
            status:
              type: string
              example: healthy
            ollama_url:
              type: string
              example: http://localhost:11434
            model:
              type: string
              example: mistral
    """
    return jsonify({
        "status": "healthy",
        "ollama_url": settings.OLLAMA_BASE_URL,
        "model": settings.OLLAMA_MODEL
    }), 200


def create_app():
    """Factory function para crear la aplicación Flask (útil para testing)"""
    return app


def main():
    """Inicia el servidor Flask"""
    import sys
    import io
    
    # Configurar encoding UTF-8 para stdout en Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 60)
    print("  Log Analyzer API")
    print("=" * 60)
    print()
    print(f"  Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"  Modelo: {settings.OLLAMA_MODEL}")
    print(f"  Output: {settings.OUT_DIR}")
    print()
    # Usar versión sin emojis para compatibilidad Windows
    print("  WARNING: Esta API no tiene autenticacion. No exponer en produccion sin seguridad.")
    print("  WARNING: Riesgo de prompt injection si los logs contienen instrucciones maliciosas.")
    print()
    print("=" * 60)
    print()
    print("Endpoints disponibles:")
    print("  GET  /           - Info de la API")
    print("  GET  /health     - Health check")
    print("  GET  /datasets   - Listar archivos disponibles")
    print("  POST /reports/download - Descargar reporte en formato")
    print("  POST /analyze    - Analizar logs")
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
