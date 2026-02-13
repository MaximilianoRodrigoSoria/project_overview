"""
Adapter de lectura de logs desde filesystem.
Implementa LogReaderPort para leer archivos locales.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional

from ..ports.log_reader_port import LogReaderPort
from ..config.constants import Constants


logger = logging.getLogger(__name__)


class FileSystemLogReader(LogReaderPort):
    """Lee logs desde archivos del sistema de archivos local"""
    
    def read_log(self, source: str) -> str:
        """
        Lee un archivo de logs del filesystem.
        
        Args:
            source: Path al archivo de logs
        
        Returns:
            Contenido del archivo como string
        
        Raises:
            FileNotFoundError: Si el archivo no existe
            IOError: Si hay error de lectura
        """
        path = Path(source)
        
        if not path.exists():
            logger.error(f"{Constants.ERROR_FILE_NOT_FOUND}: {source}")
            raise FileNotFoundError(f"Archivo no encontrado: {source}")
        
        if not path.is_file():
            logger.error(f"La ruta no es un archivo: {source}")
            raise ValueError(f"La ruta no es un archivo: {source}")
        
        logger.debug(f"Leyendo archivo: {source}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.debug(f"Archivo leído: {len(content)} caracteres")
            return content
            
        except Exception as e:
            logger.error(f"Error al leer archivo {source}: {e}")
            raise IOError(f"Error al leer archivo: {e}") from e

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
        dir_path = Path(directory)
        
        if not dir_path.exists():
            logger.error(f"{Constants.ERROR_FILE_NOT_FOUND}: {directory}")
            raise FileNotFoundError(f"Directorio no encontrado: {directory}")
        
        if not dir_path.is_dir():
            logger.error(f"La ruta no es un directorio: {directory}")
            raise ValueError(f"La ruta no es un directorio: {directory}")
        
        logger.debug(f"Listando archivos en: {directory}")
        
        try:
            logs = []
            for file_path in sorted(dir_path.glob("*.txt")):
                if file_path.is_file():
                    logs.append({
                        "name": file_path.name,
                        "path": str(file_path.absolute()),
                        "size_bytes": file_path.stat().st_size
                    })
            
            logger.debug(f"Se encontraron {len(logs)} archivos de log")
            return logs
            
        except Exception as e:
            logger.error(f"Error al listar archivos en {directory}: {e}")
            raise IOError(f"Error al listar directorio: {e}") from e
