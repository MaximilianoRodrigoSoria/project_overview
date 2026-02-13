"""
Entrypoint CLI para log_analyzer.
Permite ejecutar el análisis de logs desde línea de comandos.

Uso:
    python app/cli.py --input datasets/generated_logs.txt
    python app/cli.py --input datasets/generated_logs.txt --output ./custom_out
"""

import argparse
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.logging_config import setup_logging
from src.config.settings import settings
from src.config.constants import Constants
from src.domain.use_cases import GenerateReportUseCase
from src.adapters.log_reader_fs import FileSystemLogReader
from src.domain.log_analyzer.analyzer import LogAnalyzer
from src.adapters.llm_factory import create_llm
from src.adapters.cache_memory import MemoryCache
from src.adapters.report_writer_fs import FileSystemReportWriter


def main():
    """Punto de entrada principal del CLI"""
    # Parsear argumentos
    parser = argparse.ArgumentParser(
        description="Log Analyzer - Genera reportes profesionales de análisis de logs usando LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python app/cli.py --input datasets/generated_logs.txt
  python app/cli.py --input /path/to/app.log --output ./reports

Variables de entorno soportadas:
  OLLAMA_BASE_URL       URL de Ollama (default: http://localhost:11434)
  OLLAMA_MODEL          Modelo a usar (default: mistral)
  OUT_DIR               Directorio de salida (default: ./out)
  LOG_LEVEL             Nivel de logging (default: INFO)
  REQUEST_TIMEOUT_SECONDS  Timeout de requests (default: 120)
        """
    )
    
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path al archivo de logs a analizar"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help=f"Directorio de salida (default: {settings.OUT_DIR})"
    )
    
    parser.add_argument(
        "--run-id",
        type=str,
        help="Identificador único para esta ejecución (se genera automáticamente si no se provee)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        help="Nivel de logging para esta ejecución"
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(level=args.log_level)
    
    # Sobrescribir OUT_DIR si se especifica
    if args.output:
        settings.OUT_DIR = Path(args.output)
        settings.REPORTS_DIR = settings.OUT_DIR / "reports"
        settings.ANALYSIS_DIR = settings.OUT_DIR / "analysis"
    
    # Validar archivo de entrada
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] {Constants.ERROR_FILE_NOT_FOUND}: {args.input}")
        return 1
    
    print(f"[INFO] Log Analyzer CLI")
    print(f"[INFO] Archivo de entrada: {input_path}")
    print(f"[INFO] Directorio de salida: {settings.OUT_DIR}")
    print(f"[INFO] Proveedor LLM: {settings.LLM_PROVIDER}")
    print()
    
    try:
        # Componer dependencias (inyección manual)
        log_reader = FileSystemLogReader()
        analyzer = LogAnalyzer()
        llm = create_llm()
        cache = MemoryCache()
        report_writer = FileSystemReportWriter()
        
        # Crear caso de uso
        use_case = GenerateReportUseCase(
            log_reader=log_reader,
            analyzer=analyzer,
            llm=llm,
            report_writer=report_writer,
            cache=cache
        )
        
        # Ejecutar
        print("[INFO] Iniciando análisis...")
        result = use_case.execute(
            log_path=str(input_path),
            run_id=args.run_id
        )
        
        # Mostrar resultado
        print()
        print("[OK] Analisis completado exitosamente!")
        print()
        print(f"Run ID: {result.run_id}")
        print("Reportes:")
        for report_format, report_path in result.report_paths.items():
            print(f"  - {report_format}: {report_path}")
        print(f"Análisis JSON: {result.analysis_path}")
        print()
        print("Resumen:")
        print(f"  - Total eventos: {result.summary['total_events']}")
        print(f"  - Errores: {result.summary['total_errors']}")
        print(f"  - Warnings: {result.summary['total_warnings']}")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        print()
        print("[WARN] Proceso interrumpido por el usuario")
        return 130
        
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return 1
        
    except ConnectionError as e:
        print(f"[ERROR] Error de conexión: {e}")
        print(f"[HINT] Verifica que Ollama esté corriendo en {settings.OLLAMA_BASE_URL}")
        return 1
        
    except TimeoutError as e:
        print(f"[ERROR] {e}")
        print(f"[HINT] Considera aumentar REQUEST_TIMEOUT_SECONDS (actual: {settings.REQUEST_TIMEOUT_SECONDS}s)")
        return 1
        
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
