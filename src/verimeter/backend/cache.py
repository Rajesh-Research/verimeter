import json
import logging
from typing import Optional, Any
from verimeter.backend.config import settings

logger = logging.getLogger("verimeter.backend.cache")

class RedisCacheManager:
    def __init__(self):
        self.use_redis = False
        self.local_cache = {}
        
        try:
            import redis
            # Connect to Redis
            self.client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            # Verify connection
            self.client.ping()
            self.use_redis = True
            logger.info(f"Connected to Redis cache at {settings.REDIS_URL}")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Falling back to in-memory local dict cache.")
            
    def get(self, key: str) -> Optional[Any]:
        """
        Gets a value from Redis or local in-memory dict.
        """
        if self.use_redis:
            try:
                val = self.client.get(key)
                if val:
                    return json.loads(val.decode())
            except Exception as e:
                logger.error(f"Redis get failed: {e}")
                
        # Local fallback
        return self.local_cache.get(key)
        
    def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """
        Sets a JSON-serializable value in Redis or local dict.
        """
        if self.use_redis:
            try:
                self.client.setex(key, expire_seconds, json.dumps(value))
                return True
            except Exception as e:
                logger.error(f"Redis set failed: {e}")
                
        # Local fallback
        self.local_cache[key] = value
        return True

    def delete(self, key: str) -> bool:
        """
        Removes a key from cache.
        """
        if self.use_redis:
            try:
                self.client.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete failed: {e}")
                
        # Local fallback
        if key in self.local_cache:
            del self.local_cache[key]
        return True

cache_manager = RedisCacheManager()
