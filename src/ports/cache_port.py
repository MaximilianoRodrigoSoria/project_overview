"""
Port para cache de resultados.
Define la interfaz para cache in-memory con TTL.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class CachePort(ABC):
    """Interfaz para cache con expiracion por TTL"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del cache si existe y no expiro.

        Args:
            key: Identificador del cache

        Returns:
            Valor almacenado o None si no existe o expiro
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        """
        Guarda un valor en cache con TTL.

        Args:
            key: Identificador del cache
            value: Valor a almacenar
            ttl_seconds: Tiempo de vida en segundos
        """
        pass

    @abstractmethod
    def invalidate(self, key: str) -> None:
        """
        Invalida una entrada del cache.

        Args:
            key: Identificador del cache
        """
        pass
