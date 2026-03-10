# app/utils/cache_service.py

from flask_caching import Cache
from functools import wraps

cache = Cache()

def cache_response(timeout=300, key_prefix='view_'):
    """Decorator to cache view responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"{key_prefix}{f.__name__}_{str(kwargs)}"
            cached = cache.get(cache_key)
            
            if cached:
                return cached
            
            response = f(*args, **kwargs)
            cache.set(cache_key, response, timeout=timeout)
            return response
        return decorated_function
    return decorator

def invalidate_cache(pattern):
    """Invalidate cache entries matching a pattern"""
    keys = cache.cache._cache.keys()
    for key in keys:
        if pattern in key:
            cache.delete(key)

class CacheService:
    """Service for managing cache"""
    
    @staticmethod
    def clear_user_cache(user_id):
        """Clear all cache entries for a user"""
        invalidate_cache(f'user_{user_id}')
        invalidate_cache(f'notifications_{user_id}')
        invalidate_cache(f'medications_{user_id}')
    
    @staticmethod
    def get_or_set(key, func, timeout=300, *args, **kwargs):
        """Get cached value or set it if not exists"""
        cached = cache.get(key)
        if cached:
            return cached
        
        value = func(*args, **kwargs)
        cache.set(key, value, timeout=timeout)
        return value