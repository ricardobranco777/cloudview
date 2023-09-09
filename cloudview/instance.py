"""
Instance class
"""

import logging
from typing import Any

from cachetools import cached, TTLCache
from libcloud.compute.types import NodeState, LibcloudError
from requests.exceptions import RequestException

from cloudview.singleton import Singleton2
from cloudview.utils import exception

CACHED_SECONDS = 300
STATES = [str(getattr(NodeState, _)) for _ in dir(NodeState) if _.isupper()]


class Instance:
    """
    Instance class
    """

    def __init__(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __repr__(self) -> str:
        attrs = [x for x in dir(self) if not callable(x) and not x.startswith("_")]
        return (
            f"{type(self).__name__}("
            + ", ".join(
                [
                    f"{x}={repr(getattr(self, x))}"
                    if getattr(self, x) is not None
                    else f"{x}=None"
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

    def __repr__(self) -> str:
        return f'{type(self).__name__}(cloud="{self.cloud}")'

    @cached(cache=TTLCache(maxsize=1, ttl=300))
    def _get_instances(self) -> list[Instance]:
        raise NotImplementedError("CSP._get_instances needs to be overridden")

    def get_instances(self) -> list[Instance]:
        """
        Get instances
        """
        try:
            return self._get_instances()
        except (LibcloudError, RequestException) as exc:
            logging.error(
                "%s: %s: %s", self.__class__.__name__, self.cloud, exception(exc)
            )
            return []

    def _get_instance(self, instance_id: str, params: dict) -> Instance:
        raise NotImplementedError("CSP._get_instance needs to be overridden")

    def get_instance(self, instance_id: str, **params) -> Instance:
        """
        Get instance by id
        """
        try:
            return self._get_instance(instance_id, params)
        except (LibcloudError, RequestException) as exc:
            logging.error(
                "%s: %s: %s: %s",
                self.__class__.__name__,
                self.cloud,
                instance_id,
                exception(exc),
            )
            raise LibcloudError(f"{exc}") from exc
