"""
Cache in-memory con TTL.
"""

import logging
import time
from typing import Any, Dict, Optional, Tuple

from ..ports.cache_port import CachePort


logger = logging.getLogger(__name__)


class MemoryCache(CachePort):
    """Cache in-memory con expiracion por TTL"""

    def __init__(self):
        self._store: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del cache si existe y no expiro.

        Args:
            key: Identificador del cache

        Returns:
            Valor almacenado o None
        """
        entry = self._store.get(key)
        if entry is None:
            return None

        value, expires_at = entry
        if time.time() >= expires_at:
            logger.debug("Cache expired: %s", key)
            self._store.pop(key, None)
            return None

        return value

    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        """
        Guarda un valor en cache con TTL.

        Args:
            key: Identificador del cache
            value: Valor a almacenar
            ttl_seconds: Tiempo de vida en segundos
        """
        expires_at = time.time() + ttl_seconds
        self._store[key] = (value, expires_at)

    def invalidate(self, key: str) -> None:
        """
        Invalida una entrada del cache.

        Args:
            key: Identificador del cache
        """
        self._store.pop(key, None)
