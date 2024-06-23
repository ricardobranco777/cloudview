"""
Singleton metaclasses
"""

import threading


class Singleton(type):
    """
    Singleton metaclass
    """

    def __init__(cls, name, bases, attrs) -> None:
        super().__init__(name, bases, attrs)
        cls._singleton_instance = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton_instance is None:
            cls._singleton_instance = super().__call__(*args, **kwargs)
        return cls._singleton_instance


class Singleton2(type):
    """
    Singleton metaclass that considers arguments
    """

    def __init__(cls, name, bases, attrs) -> None:
        super().__init__(name, bases, attrs)
        cls._singleton_instances: dict[tuple, type] = {}
        cls.__singleton_lock = threading.RLock()

    def __call__(cls, *args, **kwargs):
        key = (cls, args, frozenset(kwargs.items()))
        if key not in cls._singleton_instances:
            with cls.__singleton_lock:
                if key not in cls._singleton_instances:
                    cls._singleton_instances[key] = super().__call__(*args, **kwargs)
        return cls._singleton_instances[key]
