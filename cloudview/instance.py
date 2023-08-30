"""
Instance class
"""

import logging
from typing import Any

from cachetools import cached, TTLCache
from libcloud.compute.types import NodeState

from cloudview.singleton import Singleton2

STATES = [str(getattr(NodeState, _)) for _ in dir(NodeState) if _.isupper()]


class Instance:
    """
    Instance class
    """

    def __init__(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __repr__(self):
        attrs = [x for x in dir(self) if not callable(x) and not x.startswith("_")]
        return (
            f"{type(self).__name__}("
            + ", ".join(
                [
                    f'{x}="{getattr(self, x)}"'
                    if isinstance(x, str)
                    else f"{x}={getattr(self, x)}"
                    for x in attrs
                ]
            )
            + ")"
        )

    # Allow access this object as a dictionary

    def __getitem__(self, item: str):
        try:
            return getattr(self, item)
        except AttributeError as exc:
            raise KeyError(exc) from exc

    def __setitem__(self, item: str, value: Any):
        setattr(self, item, value)

    def __delitem__(self, item: str):
        try:
            delattr(self, item)
        except AttributeError as exc:
            raise KeyError(exc) from exc


class CSP(metaclass=Singleton2):
    """
    Cloud Service Provider class
    """

    def __init__(self, cloud: str = ""):
        self.cloud = cloud or "_"

    def __repr__(self):
        return f'{type(self).__name__}(cloud="{self.cloud}")'

    def _get_instances(self) -> list[Instance]:
        """
        Method to be overriden
        """
        assert False
        return []

    @cached(cache=TTLCache(maxsize=1, ttl=300))
    def get_instances(self) -> list[Instance]:
        """
        Cached get_instances()
        """
        return self._get_instances()

    def _get_instance(self, identifier: str, params: dict) -> Instance | None:
        """
        Get instance
        """
        raise NotImplementedError("CSP._get_instance needs to be overridden")

    @cached(cache=TTLCache(maxsize=64, ttl=60))
    def get_instance(self, identifier: str, **params) -> dict | None:
        """
        Get instance by id
        """
        if self.get_instances.cache.currsize:  # pylint: disable=no-member
            for instance in self.get_instances():
                if instance.identifier == identifier:
                    logging.debug(
                        "get_instance: returning cached info for %s", identifier
                    )
                    return instance.extra
        instance = self._get_instance(identifier, params)  # type: ignore
        if instance is None:
            return None
        return instance.extra
