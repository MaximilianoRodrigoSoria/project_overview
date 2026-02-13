"""
Port para lectura de logs.
Define la interfaz de entrada de datos de logs.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class LogReaderPort(ABC):
    """Interfaz para leer logs desde diferentes fuentes"""
    
    @abstractmethod
    def read_log(self, source: str) -> str:
        """
        Lee el contenido de un log.
        
        Args:
            source: Identificador de la fuente (path, URL, etc.)
        
        Returns:
            Contenido del log como string
        
        Raises:
            FileNotFoundError: Si la fuente no existe
            IOError: Si hay error de lectura
        """
        pass

    @abstractmethod
    def list_logs(self, directory: str) -> List[Dict[str, Optional[int]]]:
        """
        Lista todos los logs disponibles en un directorio.
        
        Args:
            directory: Ruta del directorio a listar
        
        Returns:
            Lista de diccionarios con {name: str, size_bytes: int, path: str}
        
        Raises:
            FileNotFoundError: Si el directorio no existe
            IOError: Si hay error de lectura del directorio
        """
        pass
