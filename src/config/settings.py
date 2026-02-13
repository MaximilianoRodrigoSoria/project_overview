"""
Configuración centralizada del proyecto log_analyzer.
Lee variables de entorno con defaults razonables.
"""

import os
from pathlib import Path


class Settings:
    """
    Clase de configuración que lee parámetros desde variables de entorno
    con valores por defecto razonables.
    """
    
    def __init__(self):
        # Detectar el directorio raíz del proyecto
        # Este archivo está en src/config/settings.py, el raíz está 2 niveles arriba
        self._project_root = Path(__file__).parent.parent.parent
        
        # Proveedor LLM
        self.LLM_PROVIDER = os.environ.get(
            "LLM_PROVIDER",
            "ollama"
        ).lower()

        # Ollama / LLM
        self.OLLAMA_BASE_URL = os.environ.get(
            "OLLAMA_BASE_URL",
            "http://localhost:11434"
        )
        
        self.OLLAMA_MODEL = os.environ.get(
            "OLLAMA_MODEL",
            "mistral"
        )

        # OpenAI
        self.OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
        self.OPENAI_MODEL = os.environ.get(
            "OPENAI_MODEL",
            "gpt-4o-mini"
        )

        # Anthropic
        self.ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
        self.ANTHROPIC_MODEL = os.environ.get(
            "ANTHROPIC_MODEL",
            "claude-sonnet-4-20250514"
        )

        # Google
        self.GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
        self.GOOGLE_MODEL = os.environ.get(
            "GOOGLE_MODEL",
            "gemini-1.5-flash"
        )
        
        # Directorio de salida (convertir a ruta absoluta si es relativa)
        out_dir_str = os.environ.get("OUT_DIR", "./out")
        self.OUT_DIR = Path(out_dir_str)
        if not self.OUT_DIR.is_absolute():
            self.OUT_DIR = self._project_root / self.OUT_DIR

        # Directorio de datasets (convertir a ruta absoluta si es relativa)
        datasets_dir_str = os.environ.get("DATASETS_DIR", "./datasets")
        self.DATASETS_DIR = Path(datasets_dir_str)
        if not self.DATASETS_DIR.is_absolute():
            self.DATASETS_DIR = self._project_root / self.DATASETS_DIR
        
        # Límite de archivos para descargar reportes
        self.REPORT_DOWNLOAD_MAX_FILES = int(os.environ.get(
            "REPORT_DOWNLOAD_MAX_FILES",
            "10"
        ))

        # Cache
        self.CACHE_ENABLED = os.environ.get(
            "CACHE_ENABLED",
            "true"
        ).lower() == "true"
        self.CACHE_TTL_SECONDS = int(os.environ.get(
            "CACHE_TTL_SECONDS",
            "60"
        ))

        # Reporte
        self.REPORT_FORMAT = os.environ.get(
            "REPORT_FORMAT",
            "excel"
        ).lower()
        
        # Nivel de logging
        self.LOG_LEVEL = os.environ.get(
            "LOG_LEVEL",
            "INFO"
        ).upper()
        
        # Timeout para requests HTTP
        self.REQUEST_TIMEOUT_SECONDS = int(os.environ.get(
            "REQUEST_TIMEOUT_SECONDS",
            "120"
        ))
        
        # Endpoint completo de generación de Ollama
        self.OLLAMA_GENERATE_URL = f"{self.OLLAMA_BASE_URL}/api/generate"
        
        # Paths derivados
        self.REPORTS_DIR = self.OUT_DIR / "reports"
        self.ANALYSIS_DIR = self.OUT_DIR / "analysis"
    
    def ensure_output_dirs(self):
        """Crea los directorios de salida si no existen"""
        self.OUT_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    
    def __repr__(self):
        return (
            f"Settings("
            f"LLM_PROVIDER={self.LLM_PROVIDER}, "
            f"OLLAMA_BASE_URL={self.OLLAMA_BASE_URL}, "
            f"OLLAMA_MODEL={self.OLLAMA_MODEL}, "
            f"OPENAI_MODEL={self.OPENAI_MODEL}, "
            f"ANTHROPIC_MODEL={self.ANTHROPIC_MODEL}, "
            f"GOOGLE_MODEL={self.GOOGLE_MODEL}, "
            f"CACHE_ENABLED={self.CACHE_ENABLED}, "
            f"CACHE_TTL_SECONDS={self.CACHE_TTL_SECONDS}, "
            f"REPORT_FORMAT={self.REPORT_FORMAT}, "
            f"OUT_DIR={self.OUT_DIR}, "
            f"DATASETS_DIR={self.DATASETS_DIR}, "
            f"REPORT_DOWNLOAD_MAX_FILES={self.REPORT_DOWNLOAD_MAX_FILES}, "
            f"LOG_LEVEL={self.LOG_LEVEL}, "
            f"REQUEST_TIMEOUT_SECONDS={self.REQUEST_TIMEOUT_SECONDS})"
        )


# Instancia global por defecto (singleton simple)
settings = Settings()
