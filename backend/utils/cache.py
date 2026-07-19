"""
NetElixIQ AI — TTL-based Disk Cache
Adapted from consultantOS caching pattern.
"""
import hashlib
import json
import logging
from typing import Any, Optional

import diskcache

from backend.config import settings

logger = logging.getLogger(__name__)

_cache: Optional[diskcache.Cache] = None


def _get_cache() -> diskcache.Cache:
    global _cache
    if _cache is None:
        _cache = diskcache.Cache(directory=settings.cache_dir)
    return _cache


def make_cache_key(*args) -> str:
    """Create a deterministic cache key from arguments."""
    raw = json.dumps(args, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache. Returns None on miss."""
    try:
        return _get_cache().get(key)
    except Exception as e:
        logger.debug(f"Cache get failed: {e}")
        return None


def cache_set(key: str, value: Any, ttl: int = None) -> bool:
    """Set a value in cache with optional TTL override."""
    ttl = ttl or settings.cache_ttl_seconds
    try:
        _get_cache().set(key, value, expire=ttl)
        return True
    except Exception as e:
        logger.debug(f"Cache set failed: {e}")
        return False


def cache_delete(key: str) -> None:
    """Delete a key from cache."""
    try:
        _get_cache().delete(key)
    except Exception:
        pass


def cache_clear() -> None:
    """Clear entire cache."""
    try:
        _get_cache().clear()
    except Exception:
        pass
