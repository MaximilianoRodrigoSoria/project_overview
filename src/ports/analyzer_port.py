"""
Port para análisis de logs.
Define la interfaz para analizar y extraer información de logs.
"""

from abc import ABC, abstractmethod
from typing import Dict


class AnalyzerPort(ABC):
    """Interfaz para analizar logs y extraer estructura"""
    
    @abstractmethod
    def analyze(self, log_text: str) -> Dict:
        """
        Analiza el texto de logs y extrae información estructurada.
        
        Args:
            log_text: Texto completo del log
        
        Returns:
            Diccionario con el análisis estructurado:
            {
                "summary": {"total_events": int, "total_errors": int, ...},
                "error_groups": [...],
                "warnings": [...],
                "events": [...]
            }
        """
        pass
