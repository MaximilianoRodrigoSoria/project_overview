"""
Port para integración con LLM.
Define la interfaz para generación de texto con modelos de lenguaje.
"""

from abc import ABC, abstractmethod
from typing import Optional


class LLMPort(ABC):
    """Interfaz para interactuar con LLMs"""
    
    @abstractmethod
    def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Genera texto usando el LLM.
        
        Args:
            prompt: Prompt principal para el LLM
            system_prompt: Prompt de sistema (opcional)
        
        Returns:
            Texto generado por el LLM
        
        Raises:
            ConnectionError: Si no se puede conectar al LLM
            TimeoutError: Si el request excede el timeout
            Exception: Otros errores de generación
        """
        pass
