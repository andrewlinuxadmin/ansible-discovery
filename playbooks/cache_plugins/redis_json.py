# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Andre Carlos <andre.carlos@redhat.com>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import time
from ansible.plugins.cache import BaseCacheModule
from ansible.errors import AnsibleError

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

DOCUMENTATION = '''
cache: redis_json
short_description: RedisJSON optimized cache plugin for Grafana dashboards
description:
    - This cache plugin stores Ansible facts directly as RedisJSON structures
    - Optimized for Grafana queries with JSONPath navigation
    - Eliminates need for post-processing migration scripts
    - Provides structured data with counters and metadata
version_added: "2.9"
requirements:
    - redis >= 3.0.0 (python library)
    - Redis Stack with RedisJSON module
options:
    _uri:
        description:
            - Redis connection string
        default: redis://localhost:6379/0
        env:
            - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
            - key: fact_caching_connection
              section: defaults
    _prefix:
        description:
            - Redis key prefix for all cache entries
        default: ansible_facts
        env:
            - name: ANSIBLE_CACHE_PLUGIN_PREFIX
        ini:
            - key: fact_caching_prefix
              section: defaults
    _timeout:
        description:
            - Cache expiration timeout in seconds (0 = never expire)
        default: 0
        type: integer
        env:
            - name: ANSIBLE_CACHE_PLUGIN_TIMEOUT
        ini:
            - key: fact_caching_timeout
              section: defaults
'''


class CacheModule(BaseCacheModule):
    """
    RedisJSON cache plugin optimized for Grafana dashboards.
    
    Stores Ansible facts in structured RedisJSON format with:
    - host_info: Basic host information
    - discovery: Discovered processes and services
    - services: Service status information
    - network: Network configuration
    - stats: Counters for dashboard metrics
    - _metadata: Cache metadata and timestamps
    """

    def __init__(self, *args, **kwargs):
        super(CacheModule, self).__init__(*args, **kwargs)
        
        if not HAS_REDIS:
            raise AnsibleError(
                "redis python module is required for redis_json cache plugin"
            )
        
        # Parse connection string
        connection = self.get_option('_uri')
        self._timeout = self.get_option('_timeout')
        self._prefix = self.get_option('_prefix')
        
        try:
            # Parse Redis URL
            self._db = redis.from_url(connection, decode_responses=True)
            # Test RedisJSON availability
            try:
                self._db.execute_command(
                    'JSON.GET', 'test_redisjson_availability', '$'
                )
            except redis.ResponseError as e:
                if 'unknown command' in str(e).lower():
                    raise AnsibleError(
                        "RedisJSON module not available. "
                        "Please install Redis Stack or load RedisJSON module."
                    )
        except Exception as e:
            raise AnsibleError("Failed to connect to Redis: %s" % str(e))

    def _make_key(self, key):
        """Create the full Redis key with prefix."""
        return f"{self._prefix}{key}"

    def _transform_to_redisjson(self, data):
        """
        Transform Ansible facts to RedisJSON structure optimized for Grafana.
        
        Creates a generic structure that works with any Ansible data:
        {
            "host_info": { extracted basic host information },
            "ansible_facts": { all ansible_* variables },
            "custom_facts": { non-ansible variables from playbooks },
            "stats": { computed metrics for dashboards },
            "_metadata": { cache metadata }
        }
        """
        if not isinstance(data, dict):
            # Handle non-dict data by wrapping it
            return {
                "raw_data": data,
                "_metadata": {
                    "timestamp": int(time.time()),
                    "format_version": "1.0",
                    "source": "ansible_cache_redis_json"
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
            "distribution": ansible_facts.get(
                'ansible_distribution', 'unknown'
            ),
            "distribution_version": ansible_facts.get(
                'ansible_distribution_version', 'unknown'
            ),
            "os_family": ansible_facts.get('ansible_os_family', 'unknown'),
            "architecture": ansible_facts.get(
                'ansible_architecture', 'unknown'
            ),
            "kernel": ansible_facts.get('ansible_kernel', 'unknown'),
            "python_version": ansible_facts.get(
                'ansible_python_version', 'unknown'
            ),
            "uptime": ansible_facts.get('ansible_uptime_seconds', 0)
        }
        
        # Extract network information
        network = {
            "interfaces": ansible_facts.get('ansible_interfaces', []),
            "default_ipv4": ansible_facts.get('ansible_default_ipv4', {}),
            "default_ipv6": ansible_facts.get('ansible_default_ipv6', {}),
            "dns": ansible_facts.get('ansible_dns', {}),
            "hostname": ansible_facts.get('ansible_hostname', 'unknown'),
            "fqdn": ansible_facts.get('ansible_fqdn', 'unknown')
        }
        
        # Add interface details
        interface_details = {}
        for interface in network['interfaces']:
            iface_key = f'ansible_{interface}'
            if iface_key in ansible_facts:
                interface_details[interface] = ansible_facts[iface_key]
        network['interface_details'] = interface_details
        
        # Extract services information (generic)
        services = {}
        if 'services' in custom_facts:
            services = custom_facts['services']
        elif 'ansible_facts' in data and 'services' in data['ansible_facts']:
            services = data['ansible_facts']['services']
        
        # Generate generic statistics for dashboards
        stats = {
            "ansible_facts_count": len(ansible_facts),
            "custom_facts_count": len(custom_facts),
            "interface_count": len(network['interfaces']),
            "last_updated": str(int(time.time()))
        }
        
        # Add memory stats if available
        if 'ansible_memtotal_mb' in ansible_facts:
            stats['memory_total_mb'] = ansible_facts['ansible_memtotal_mb']
        if 'ansible_memfree_mb' in ansible_facts:
            stats['memory_free_mb'] = ansible_facts['ansible_memfree_mb']
        
        # Add CPU stats if available
        if 'ansible_processor_count' in ansible_facts:
            stats['cpu_count'] = ansible_facts['ansible_processor_count']
        if 'ansible_processor_cores' in ansible_facts:
            stats['cpu_cores'] = ansible_facts['ansible_processor_cores']
        
        # Add disk stats if available
        if 'ansible_mounts' in ansible_facts:
            mounts = ansible_facts['ansible_mounts']
            total_size = sum(mount.get('size_total', 0) for mount in mounts)
            total_available = sum(
                mount.get('size_available', 0) for mount in mounts
            )
            stats['disk_total_bytes'] = total_size
            stats['disk_available_bytes'] = total_available
            stats['disk_used_bytes'] = total_size - total_available
            stats['mount_points_count'] = len(mounts)
        
        # Add service stats if available
        if services:
            running_services = [
                s for s in services.values()
                if isinstance(s, dict) and s.get('state') == 'running'
            ]
            stats['services_total'] = len(services)
            stats['services_running'] = len(running_services)
        
        # Count different types of custom facts for insight
        custom_fact_types = {}
        for key, value in custom_facts.items():
            if isinstance(value, list):
                custom_fact_types[f'{key}_count'] = len(value)
            elif isinstance(value, dict):
                custom_fact_types[f'{key}_keys_count'] = len(value.keys())
            elif isinstance(value, bool):
                custom_fact_types[f'{key}_flag'] = value
        
        stats.update(custom_fact_types)
        
        # Create the final structured data
        structured_data = {
            "host_info": host_info,
            "ansible_facts": ansible_facts,
            "custom_facts": custom_facts,
            "network": network,
            "services": services,
            "stats": stats,
            "_metadata": {
                "timestamp": int(time.time()),
                "format_version": "1.0",
                "source": "ansible_cache_redis_json",
                "original_keys": list(data.keys()),
                "transformation_date": time.strftime(
                    "%Y-%m-%d %H:%M:%S UTC", time.gmtime()
                )
            },
            "_raw": data  # Keep original data for fallback/debugging
        }
        
        return structured_data

    def get(self, key):
        """Retrieve value from Redis cache."""
        redis_key = self._make_key(key)
        try:
            # Try to get as RedisJSON first
            result = self._db.execute_command('JSON.GET', redis_key, '$')
            if result:
                # RedisJSON returns a JSON string, parse it
                data = json.loads(result)
                # RedisJSON GET with JSONPath returns an array,
                # get first element
                if isinstance(data, list) and len(data) > 0:
                    # Return original data for Ansible compatibility
                    return data[0].get('_raw', data[0])
                return data
            return None
        except redis.ResponseError:
            # Fallback to regular Redis GET if JSON.GET fails
            try:
                result = self._db.get(redis_key)
                if result:
                    return json.loads(result)
                return None
            except (ValueError, TypeError):
                return None
        except Exception:
            return None

    def set(self, key, value):
        """Store value in Redis as RedisJSON."""
        redis_key = self._make_key(key)
        
        try:
            # Transform data to optimized RedisJSON structure
            structured_data = self._transform_to_redisjson(value)
            
            # Store as RedisJSON
            self._db.execute_command(
                'JSON.SET', redis_key, '$', json.dumps(structured_data)
            )
            
            # Set expiration if configured
            if self._timeout > 0:
                self._db.expire(redis_key, self._timeout)
                
        except Exception as e:
            # Fallback to regular Redis if RedisJSON fails
            try:
                timeout = self._timeout or -1
                self._db.setex(redis_key, timeout, json.dumps(value))
            except Exception as fallback_error:
                error_msg = (
                    f"Failed to cache data: RedisJSON error: {e}, "
                    f"Fallback error: {fallback_error}"
                )
                raise AnsibleError(error_msg)

    def delete(self, key):
        """Remove key from Redis cache."""
        redis_key = self._make_key(key)
        return self._db.delete(redis_key)

    def has_key(self, key):
        """Check if key exists in Redis cache."""
        redis_key = self._make_key(key)
        return self._db.exists(redis_key)

    def contains(self, key):
        """Check if key exists in Redis cache (required by BaseCacheModule)."""
        return self.has_key(key)

    def keys(self):
        """Return all cache keys."""
        pattern = f"{self._prefix}*"
        keys = self._db.keys(pattern)
        return [key.replace(self._prefix, '') for key in keys]

    def flush(self):
        """Clear all cache entries."""
        pattern = f"{self._prefix}*"
        keys = self._db.keys(pattern)
        if keys:
            self._db.delete(*keys)

    def copy(self):
        """Return a copy of the cache instance."""
        return CacheModule()

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getitem__(self, key):
        result = self.get(key)
        if result is None:
            raise KeyError(key)
        return result

    def __delitem__(self, key):
        if not self.delete(key):
            raise KeyError(key)

    def __contains__(self, key):
        return self.has_key(key)

    def __iter__(self):
        return iter(self.keys())
