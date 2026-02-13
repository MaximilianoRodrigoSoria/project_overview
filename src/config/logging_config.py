"""
Configuración de logging para el proyecto log_analyzer.
Usa el módulo logging estándar de Python.
"""

import logging
import sys
from typing import Optional

from .settings import settings


# Formato de logs con prefijos claros
LOG_FORMAT = "[%(levelname)s] [%(name)s] %(message)s"

# Formato con timestamp para logs más detallados
LOG_FORMAT_DETAILED = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"


def setup_logging(
    level: Optional[str] = None,
    detailed: bool = False
) -> None:
    """
    Configura el sistema de logging global.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARN, ERROR). 
               Si es None, usa settings.LOG_LEVEL
        detailed: Si True, incluye timestamp en el formato
    """
    if level is None:
        level = settings.LOG_LEVEL
    
    log_format = LOG_FORMAT_DETAILED if detailed else LOG_FORMAT
    
    # Configurar logging raíz
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Silenciar logs verbosos de librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.
    
    Args:
        name: Nombre del módulo (típicamente __name__)
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


def log_with_run_id(logger: logging.Logger, level: int, run_id: str, message: str) -> None:
    """
    Helper para incluir run_id en los mensajes de log.
    
    Args:
        logger: Logger a usar
        level: Nivel de logging (logging.INFO, etc.)
        run_id: Identificador de la ejecución
        message: Mensaje a loggear
    """
    formatted_message = f"[run_id={run_id}] {message}"
    logger.log(level, formatted_message)
