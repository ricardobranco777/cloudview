"""
Instance class
"""

import threading
from typing import List, Optional

from cachetools import cached, TTLCache

from libcloud.compute.types import NodeState

STATES = [str(getattr(NodeState, _)) for _ in dir(NodeState) if _.isupper()]


class Instance:
    """
    Instance class
    """
    def __init__(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __getitem__(self, item: str):
        return getattr(self, item)  # Allow access this object as a dictionary


class CSP:
    """
    Cloud Service Provider class
    """
    __objects: dict = {}

    def __new__(cls, cloud: str = "", **kwargs):
        cloud = cloud or "_"
        key = (cls, cloud)
        if key not in CSP.__objects:
            CSP.__objects[key] = object.__new__(cls)
        return CSP.__objects[key]

    def __init__(self, cloud: str = ""):
        self.cloud = cloud or "_"
        self._lock = threading.Lock()

    def _get_instances(self) -> List[Instance]:
        """
        Method to be overriden
        """
        assert False
        return []

    @cached(cache=TTLCache(maxsize=1, ttl=300))
    def get_instances(self) -> List[Instance]:
        """
        Cached get_instances()
        """
        with self._lock:
            return self._get_instances()

    def _get_instance(self, key: str, value: str) -> Optional[Instance]:
        """
        Get instance by key
        """
        for instance in self.get_instances():
            if getattr(instance, key) == value:
                return instance
        return None

    def get_instance(self, instance_id: str) -> Optional[dict]:
        """
        Get instance by id
        """
        instance = self._get_instance("id", instance_id)
        if instance is not None:
            return instance.extra
        return None
