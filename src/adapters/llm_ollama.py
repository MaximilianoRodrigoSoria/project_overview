"""
Adapter de LLM usando Ollama.
Implementa LLMPort para interactuar con Ollama API local.
"""

import json
import logging
from typing import Optional

import requests

from ..ports.llm_port import LLMPort
from ..config.settings import settings
from ..config.constants import Constants


logger = logging.getLogger(__name__)


class OllamaLLM(LLMPort):
    """Cliente para Ollama API local"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Inicializa el cliente de Ollama.
        
        Args:
            base_url: URL base de Ollama (si es None, usa settings)
            model: Nombre del modelo (si es None, usa settings)
            timeout: Timeout en segundos (si es None, usa settings)
        """
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.REQUEST_TIMEOUT_SECONDS
        self.generate_url = f"{self.base_url}/api/generate"

        if not self.model:
            raise ValueError("OLLAMA_MODEL no configurado")
        
        logger.debug(
            f"OllamaLLM inicializado: {self.base_url}, modelo={self.model}"
        )
    
    def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Genera texto usando Ollama.
        
        Args:
            prompt: Prompt principal
            system_prompt: Prompt de sistema (opcional)
        
        Returns:
            Texto generado
        
        Raises:
            ConnectionError: Si no se puede conectar a Ollama
            TimeoutError: Si el request excede el timeout
            Exception: Otros errores
        """
        logger.info(f"{Constants.LOG_CALLING_LLM}: modelo={self.model}")
        logger.debug(f"Prompt length: {len(prompt)} caracteres")
        
        # Construir payload para Ollama
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            # Llamar a Ollama API
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # Parsear respuesta
            result = response.json()
            generated_text = result.get("response", "")
            
            if not generated_text:
                logger.warning("Ollama devolvió respuesta vacía")
                raise ValueError("Respuesta vacía del LLM")
            
            logger.info(
                f"Texto generado exitosamente: {len(generated_text)} caracteres"
            )
            logger.debug(f"Stats: {result.get('eval_count', '?')} tokens evaluados")
            
            return generated_text
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout al llamar a Ollama: {e}")
            raise TimeoutError(
                f"Timeout después de {self.timeout}s al llamar a Ollama"
            ) from e
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Error de conexión con Ollama: {e}")
            raise ConnectionError(
                f"No se puede conectar a Ollama en {self.base_url}"
            ) from e
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP de Ollama: {e}")
            raise Exception(f"{Constants.ERROR_LLM_FAILED}: {e}") from e
        
        except Exception as e:
            logger.error(f"Error inesperado al llamar a Ollama: {e}")
            raise Exception(f"{Constants.ERROR_LLM_FAILED}: {e}") from e
