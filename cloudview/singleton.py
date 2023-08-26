"""
Singleton metaclasses
"""

import threading


class Singleton(type):
    """
    Singleton metaclass
    """

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class Singleton2(type):
    """
    Singleton metaclass that considers arguments
    """

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls._instances = {}
        cls._lock = threading.RLock()

    def __call__(cls, *args, **kwargs):
        key = (cls, args, frozenset(kwargs.items()))
        if key not in cls._instances:
            with cls._lock:
                if key not in cls._instances:
                    cls._instances[key] = super().__call__(*args, **kwargs)
        return cls._instances[key]
