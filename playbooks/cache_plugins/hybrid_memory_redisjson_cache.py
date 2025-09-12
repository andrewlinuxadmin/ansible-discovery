# -*- coding: utf-8 -*-

"""
Hybrid Memory + Redis JSON Cache Plugin
Combines in-memory cache for current session with Redis persistence
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
from ansible.plugins.cache import BaseCacheModule
from ansible.plugins.cache.memory import CacheModule as MemoryCache

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

DOCUMENTATION = """
cache: hybrid_memory_redisjson_cache
short_description: Hybrid cache using memory and Redis
description:
    - Uses memory cache for current session performance
    - Uses Redis cache for persistence across sessions
    - Always reads ONLY from memory (never from Redis during execution)
    - Always writes to BOTH memory and Redis
    - Perfect for fresh data collection with historical storage
    - Overwrites existing Redis keys with fresh data
version_added: "1.0"
author: Andrew Carlos (@andrewlinuxadmin)
options:
    _uri:
        description: Redis connection string
        default: redis://localhost:6379/0
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
          - key: fact_caching_connection
            section: defaults
    _prefix:
        description: Key prefix for Redis storage
        default: ansible_facts
        env:
          - name: ANSIBLE_CACHE_PLUGIN_PREFIX
        ini:
          - key: fact_caching_prefix
            section: defaults
    _timeout:
        description: Cache timeout in seconds (0 = no timeout)
        default: 0
        type: int
        env:
          - name: ANSIBLE_CACHE_PLUGIN_TIMEOUT
        ini:
          - key: fact_caching_timeout
            section: defaults
"""


class CacheModule(BaseCacheModule):
    """
    Hybrid cache that combines memory and Redis caching
    """

    def __init__(self, *args, **kwargs):
        super(CacheModule, self).__init__(*args, **kwargs)
        
        # Initialize both cache backends
        self.memory_cache = MemoryCache(*args, **kwargs)
        self.redis_cache = None
        
        # Initialize Redis cache with error handling
        try:
            # Import redis library and create connection directly
            import redis
            
            # Get Redis connection settings
            redis_uri = getattr(self, 'get_option', lambda x: 'redis://localhost:6379/0')('_uri')
            redis_prefix = getattr(self, 'get_option', lambda x: 'ansible_facts')('_prefix')
            
            # Create Redis connection
            self.redis_db = redis.from_url(redis_uri, decode_responses=True)
            self.redis_prefix = redis_prefix
            
            # Test Redis connection
            self.redis_db.ping()
            display.vvv("Hybrid cache: Redis backend initialized successfully")
            display.vvv("Hybrid cache: Memory-only reads enabled by default")
        except Exception as e:
            msg = f"Hybrid cache: Failed to init Redis backend: {e}"
            display.warning(msg)
            display.warning("Hybrid cache: Falling back to memory-only mode")
            self.redis_db = None
            self.redis_prefix = ""

    def _transform_to_redisjson(self, data):
        """
        Transform Ansible facts to RedisJSON structure optimized for Grafana.
        Same transformation as redis_json plugin for compatibility.
        """
        import time
        
        if not isinstance(data, dict):
            return {
                "raw_data": data,
                "_metadata": {
                    "timestamp": int(time.time()),
                    "format_version": "1.0",
                    "source": "ansible_cache_hybrid_memory_redisjson"
                }
            }
        
        # Separate ansible built-in facts from custom facts
        ansible_facts = {}
        custom_facts = {}
        
        for key, value in data.items():
            if key.startswith('ansible_'):
                ansible_facts[key] = value
            else:
                custom_facts[key] = value
        
        # Extract basic host information from ansible facts
        host_info = {
            "hostname": ansible_facts.get('ansible_hostname', 'unknown'),
            "fqdn": ansible_facts.get('ansible_fqdn', 'unknown'),
            "distribution": ansible_facts.get('ansible_distribution', 'unknown'),
            "distribution_version": ansible_facts.get('ansible_distribution_version', 'unknown'),
            "os_family": ansible_facts.get('ansible_os_family', 'unknown'),
            "architecture": ansible_facts.get('ansible_architecture', 'unknown'),
            "kernel": ansible_facts.get('ansible_kernel', 'unknown'),
            "python_version": ansible_facts.get('ansible_python_version', 'unknown'),
            "uptime": ansible_facts.get('ansible_uptime_seconds', 0)
        }
        
        # Create structured data
        structured_data = {
            "host_info": host_info,
            "ansible_facts": ansible_facts,
            "custom_facts": custom_facts,
            "stats": {
                "ansible_facts_count": len(ansible_facts),
                "custom_facts_count": len(custom_facts),
                "last_updated": str(int(time.time()))
            },
            "_metadata": {
                "timestamp": int(time.time()),
                "format_version": "1.0",
                "source": "ansible_cache_hybrid_memory_redisjson",
                "original_keys": list(data.keys()),
                "transformation_date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            },
            "_raw": data
        }
        
        return structured_data

    def get(self, key):
        """
        Get value from cache - ALWAYS reads only from memory cache.
        Never reads from Redis to ensure fresh data collection.
        Returns empty dict if no data found to avoid Ansible errors.
        """
        try:
            value = self.memory_cache.get(key)
            if value is not None:
                msg = f"Hybrid cache: Found key '{key}' in memory cache"
                display.vvv(msg)
                return value
        except Exception as e:
            msg = f"Hybrid cache: Memory get failed for '{key}': {e}"
            display.vvv(msg)

        msg = f"Hybrid cache: Key '{key}' not found (memory-only mode)"
        display.vvv(msg)
        # Return empty dict instead of None to avoid Ansible errors
        return {}

    def set(self, key, value):
        """
        Set value in both memory and Redis caches.
        Always overwrites existing Redis keys with fresh data.
        """
        # Store in memory cache (for current session)
        try:
            self.memory_cache.set(key, value)
            msg = f"Hybrid cache: Stored key '{key}' in memory cache"
            display.vvv(msg)
        except Exception as e:
            msg = f"Hybrid cache: Failed to store in memory cache: {e}"
            display.warning(msg)

        # Store in Redis cache (for persistence) - always overwrites
        if self.redis_db:
            try:
                # Create Redis key with prefix
                redis_key = f"{self.redis_prefix}{key}"
                # Delete existing key first to ensure complete replacement
                self.redis_db.delete(redis_key)
                
                # Transform data to RedisJSON structure like redis_json plugin
                transformed_data = self._transform_to_redisjson(value)
                
                # Store as RedisJSON
                self.redis_db.execute_command('JSON.SET', redis_key, '$',
                                              json.dumps(transformed_data))
                msg = f"Hybrid cache: Stored key '{key}' as RedisJSON"
                display.vvv(msg)
            except Exception as e:
                msg = f"Hybrid cache: Failed to store in Redis cache: {e}"
                display.warning(msg)

    def delete(self, key):
        """
        Delete key from both caches.
        """
        # Delete from memory cache
        try:
            self.memory_cache.delete(key)
            msg = f"Hybrid cache: Deleted key '{key}' from memory cache"
            display.vvv(msg)
        except Exception as e:
            msg = f"Hybrid cache: Memory delete failed for '{key}': {e}"
            display.vvv(msg)

        # Delete from Redis cache
        if self.redis_db:
            try:
                redis_key = f"{self.redis_prefix}{key}"
                self.redis_db.delete(redis_key)
                msg = f"Hybrid cache: Deleted key '{key}' from Redis cache"
                display.vvv(msg)
            except Exception as e:
                msg = f"Hybrid cache: Redis delete failed for '{key}': {e}"
                display.vvv(msg)

    def flush(self):
        """
        Flush both caches.
        """
        # Flush memory cache
        try:
            self.memory_cache.flush()
            display.vvv("Hybrid cache: Flushed memory cache")
        except Exception as e:
            msg = f"Hybrid cache: Failed to flush memory cache: {e}"
            display.warning(msg)

        # Flush Redis cache
        if self.redis_db:
            try:
                # Flush only keys with our prefix
                pattern = f"{self.redis_prefix}*"
                keys = self.redis_db.keys(pattern)
                if keys:
                    self.redis_db.delete(*keys)
                display.vvv("Hybrid cache: Flushed Redis cache")
            except Exception as e:
                msg = f"Hybrid cache: Failed to flush Redis cache: {e}"
                display.warning(msg)

    def copy(self):
        """
        Return a copy of the cache.
        """
        # Use memory cache for copy (faster)
        try:
            return self.memory_cache.copy()
        except Exception as e:
            msg = f"Hybrid cache: Failed to copy from memory cache: {e}"
            display.warning(msg)
            if self.redis_db:
                try:
                    # Copy from Redis as fallback
                    pattern = f"{self.redis_prefix}*"
                    keys = self.redis_db.keys(pattern)
                    result = {}
                    for redis_key in keys:
                        key = redis_key[len(self.redis_prefix):]
                        value = self.redis_db.get(redis_key)
                        result[key] = json.loads(value) if value else None
                    return result
                except Exception as e2:
                    msg = f"Hybrid cache: Failed to copy from Redis: {e2}"
                    display.warning(msg)
            return {}

    def keys(self):
        """
        Return all keys from both caches (union).
        """
        all_keys = set()
        
        # Get keys from memory cache
        try:
            memory_keys = self.memory_cache.keys()
            all_keys.update(memory_keys)
        except Exception as e:
            msg = f"Hybrid cache: Failed to get memory keys: {e}"
            display.vvv(msg)

        # Get keys from Redis cache
        if self.redis_db:
            try:
                pattern = f"{self.redis_prefix}*"
                redis_keys = self.redis_db.keys(pattern)
                # Remove prefix from keys
                clean_keys = [k[len(self.redis_prefix):] for k in redis_keys]
                all_keys.update(clean_keys)
            except Exception as e:
                msg = f"Hybrid cache: Failed to get Redis keys: {e}"
                display.vvv(msg)

        return list(all_keys)

    def contains(self, key):
        """
        Check if key exists in either cache.
        """
        # Check memory first
        try:
            if self.memory_cache.contains(key):
                return True
        except Exception as e:
            msg = f"Hybrid cache: Memory contains failed for '{key}': {e}"
            display.vvv(msg)

        # Check Redis
        if self.redis_db:
            try:
                redis_key = f"{self.redis_prefix}{key}"
                return self.redis_db.exists(redis_key)
            except Exception as e:
                msg = f"Hybrid cache: Redis contains failed for '{key}': {e}"
                display.vvv(msg)

        return False
