"""
Generador de keys para cache de respuestas LLM.
"""

import hashlib
from typing import Optional


def build_cache_key(
    input_text: str,
    provider: str,
    model: str,
    system_prompt: Optional[str] = None
) -> str:
    """
    Genera una key deterministica basada en input y configuracion.

    Args:
        input_text: Texto de entrada del analisis
        provider: Proveedor LLM seleccionado
        model: Modelo LLM seleccionado
        system_prompt: Prompt de sistema opcional

    Returns:
        Hash SHA-256 como string
    """
    normalized_prompt = system_prompt or ""
    payload = "\n".join([provider, model, normalized_prompt, input_text])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
