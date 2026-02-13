"""
Enums del dominio log_analyzer.
Define enumeraciones para tipos y formatos.
"""

from enum import Enum


class OutputFormat(str, Enum):
    """
    Formatos de salida soportados para el endpoint /analyze.
    Usa StrEnum pattern para compatibilidad con JSON/API.
    """
    CSV = "csv"
    DOC = "doc"
    EXCEL = "excel"
    TXT = "txt"
    MARKDOWN = "markdown"
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """
        Verifica si un valor es válido para el enum.
        
        Args:
            value: String a validar
        
        Returns:
            True si es válido, False en caso contrario
        """
        if not value:
            return False
        
        try:
            cls(value.lower())
            return True
        except ValueError:
            return False
    
    @classmethod
    def values(cls) -> list:
        """Retorna todos los valores válidos del enum"""
        return [fmt.value for fmt in cls]
