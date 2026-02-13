"""
Adapter de LLM usando Anthropic via HTTP.
Implementa LLMPort para interactuar con Anthropic API.
"""

import logging
from typing import Optional

import requests

from ..ports.llm_port import LLMPort
from ..config.settings import settings
from ..config.constants import Constants


logger = logging.getLogger(__name__)


class AnthropicLLM(LLMPort):
    """Cliente HTTP para Anthropic Messages API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Inicializa el cliente Anthropic.

        Args:
            api_key: API key de Anthropic
            model: Modelo Anthropic
            timeout: Timeout en segundos
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL
        self.timeout = timeout or settings.REQUEST_TIMEOUT_SECONDS
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.api_version = "2023-06-01"

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Genera texto usando Anthropic.

        Args:
            prompt: Prompt principal
            system_prompt: Prompt de sistema (opcional)

        Returns:
            Texto generado
        """
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")

        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            content_blocks = data.get("content", [])
            if not content_blocks:
                raise ValueError("Respuesta vacia del LLM")
            content = content_blocks[0].get("text", "")
            if not content:
                raise ValueError("Respuesta vacia del LLM")
            return content
        except requests.exceptions.Timeout as e:
            logger.error("Timeout al llamar a Anthropic: %s", e)
            raise TimeoutError(
                f"Timeout despues de {self.timeout}s al llamar a Anthropic"
            ) from e
        except requests.exceptions.ConnectionError as e:
            logger.error("Error de conexion con Anthropic: %s", e)
            raise ConnectionError("No se puede conectar a Anthropic") from e
        except requests.exceptions.HTTPError as e:
            logger.error("Error HTTP de Anthropic: %s", e)
            raise Exception(f"{Constants.ERROR_LLM_FAILED}: {e}") from e
        except Exception as e:
            logger.error("Error inesperado al llamar a Anthropic: %s", e)
            raise Exception(f"{Constants.ERROR_LLM_FAILED}: {e}") from e
