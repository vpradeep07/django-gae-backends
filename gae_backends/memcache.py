"""
  Django Cache Backend for the Google App Engine
"""

from django.core.cache.backends.base import BaseCache
import time

from google.appengine.api import memcache


class MemcacheCache(BaseCache):

    def __init__(self, location, params):
        super(MemcacheCache, self).__init__(params)

    def _get_memcache_timeout(self, timeout):
        """
        Memcached deals with long (> 30 days) timeouts in a special
        way. Call this function to obtain a safe value for your timeout.
        """
        timeout = timeout or self.default_timeout
        if timeout > 2592000:  # 60*60*24*30, 30 days
            # See http://code.google.com/p/memcached/wiki/FAQ
            # "You can set expire times up to 30 days in the future. After that
            # memcached interprets it as a date, and will expire the item after
            # said date. This is a simple (but obscure) mechanic."
            #
            # This means that we have to switch to absolute timestamps.
            timeout += int(time.time())
        return timeout

    def add(self, key, value, timeout=None, version=None):
        return memcache.add(key, value, time=self._get_memcache_timeout(timeout))

    def get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)

        val = memcache.get(key)
        if val is None:
            return default
        return val

    def get_many(self, keys, version=None):
        new_keys = map(lambda x: self.make_key(x, version=version), keys)
        ret = memcache.get_multi(new_keys)
        if ret:
            _ = {}
            m = dict(zip(new_keys, keys))
            for k, v in ret.items():
                _[m[k]] = v
            ret = _
        return ret

    def incr(self, key, delta=1, version=None):
        key = self.make_key(key, version=version)

        val = memcache.incr(key, delta)
        if val is None:
            raise ValueError("Key '%s' not found" % key)
        return val

    def decr(self, key, delta=1, version=None):
        key = self.make_key(key, version=version)

        val = memcache.decr(key, delta)
        if val is None:
            raise ValueError("Key '%s' not found" % key)
        return val

    def set(self, key, value, timeout=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)

        memcache.set(key, value, time=self._get_memcache_timeout(timeout))

    def delete(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)

        memcache.delete(key)

    def set_many(self, data, timeout=0, version=None):
        safe_data = {}
        for key, value in data.items():
            key = self.make_key(key, version=version)
            safe_data[key] = value
        memcache.set_multi(safe_data, time=self._get_memcache_timeout(timeout))

    def delete_many(self, keys, version=None):
        l = lambda x: self.make_key(x, version=version)
        memcache.delete_multi(map(l, keys))

    def clear(self):
        return memcache.flush_all()


# For backwards compatibility
class CacheClass(MemcacheCache):
    pass
