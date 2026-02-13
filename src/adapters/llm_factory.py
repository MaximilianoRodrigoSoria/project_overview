"""
Factory para seleccionar proveedor LLM segun configuracion.
"""

from typing import Dict, Type

from ..ports.llm_port import LLMPort
from ..config.settings import settings
from .llm_ollama import OllamaLLM
from .llm_openai import OpenAILLM
from .llm_anthropic import AnthropicLLM
from .llm_google import GoogleLLM


PROVIDERS: Dict[str, Type[LLMPort]] = {
    "ollama": OllamaLLM,
    "openai": OpenAILLM,
    "anthropic": AnthropicLLM,
    "google": GoogleLLM
}


def create_llm() -> LLMPort:
    """
    Crea el proveedor LLM basado en settings.LLM_PROVIDER.

    Returns:
        Instancia de LLMPort

    Raises:
        ValueError: Si el proveedor no esta soportado
    """
    provider = settings.LLM_PROVIDER
    llm_cls = PROVIDERS.get(provider)
    if llm_cls is None:
        raise ValueError(f"Proveedor LLM no soportado: {provider}")
    return llm_cls()
