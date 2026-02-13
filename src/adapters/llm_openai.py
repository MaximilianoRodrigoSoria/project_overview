"""
Adapter de LLM usando OpenAI via HTTP.
Implementa LLMPort para interactuar con OpenAI API.
"""

import logging
from typing import Optional

import requests

from ..ports.llm_port import LLMPort
from ..config.settings import settings
from ..config.constants import Constants


logger = logging.getLogger(__name__)


class OpenAILLM(LLMPort):
    """Cliente HTTP para OpenAI Chat Completions"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Inicializa el cliente OpenAI.

        Args:
            api_key: API key de OpenAI
            model: Modelo OpenAI
            timeout: Timeout en segundos
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.timeout = timeout or settings.REQUEST_TIMEOUT_SECONDS
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Genera texto usando OpenAI.

        Args:
            prompt: Prompt principal
            system_prompt: Prompt de sistema (opcional)

        Returns:
            Texto generado
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no configurada")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("Respuesta vacia del LLM")
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise ValueError("Respuesta vacia del LLM")
            return content
        except requests.exceptions.Timeout as e:
            logger.error("Timeout al llamar a OpenAI: %s", e)
            raise TimeoutError(
                f"Timeout despues de {self.timeout}s al llamar a OpenAI"
            ) from e
        except requests.exceptions.ConnectionError as e:
            logger.error("Error de conexion con OpenAI: %s", e)
            raise ConnectionError("No se puede conectar a OpenAI") from e
        except requests.exceptions.HTTPError as e:
            logger.error("Error HTTP de OpenAI: %s", e)
            raise Exception(f"{Constants.ERROR_LLM_FAILED}: {e}") from e
        except Exception as e:
            logger.error("Error inesperado al llamar a OpenAI: %s", e)
            raise Exception(f"{Constants.ERROR_LLM_FAILED}: {e}") from e
