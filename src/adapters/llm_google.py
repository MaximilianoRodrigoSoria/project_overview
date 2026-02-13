"""
Adapter de LLM usando Google Gemini via HTTP.
Implementa LLMPort para interactuar con Generative Language API.
"""

import logging
from typing import Optional

import requests

from ..ports.llm_port import LLMPort
from ..config.settings import settings
from ..config.constants import Constants


logger = logging.getLogger(__name__)


class GoogleLLM(LLMPort):
    """Cliente HTTP para Google Gemini API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Inicializa el cliente Google.

        Args:
            api_key: API key de Google
            model: Modelo Gemini
            timeout: Timeout en segundos
        """
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self.model = model or settings.GOOGLE_MODEL
        self.timeout = timeout or settings.REQUEST_TIMEOUT_SECONDS

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Genera texto usando Google Gemini.

        Args:
            prompt: Prompt principal
            system_prompt: Prompt de sistema (opcional)

        Returns:
            Texto generado
        """
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY no configurada")

        base_url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        url = f"{base_url}?key={self.api_key}"

        parts = []
        if system_prompt:
            parts.append({"text": system_prompt})
        parts.append({"text": prompt})

        payload = {
            "contents": [
                {"parts": parts}
            ]
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("Respuesta vacia del LLM")
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                raise ValueError("Respuesta vacia del LLM")
            text = parts[0].get("text", "")
            if not text:
                raise ValueError("Respuesta vacia del LLM")
            return text
        except requests.exceptions.Timeout as e:
            logger.error("Timeout al llamar a Google: %s", e)
            raise TimeoutError(
                f"Timeout despues de {self.timeout}s al llamar a Google"
            ) from e
        except requests.exceptions.ConnectionError as e:
            logger.error("Error de conexion con Google: %s", e)
            raise ConnectionError("No se puede conectar a Google") from e
        except requests.exceptions.HTTPError as e:
            logger.error("Error HTTP de Google: %s", e)
            raise Exception(f"{Constants.ERROR_LLM_FAILED}: {e}") from e
        except Exception as e:
            logger.error("Error inesperado al llamar a Google: %s", e)
            raise Exception(f"{Constants.ERROR_LLM_FAILED}: {e}") from e
