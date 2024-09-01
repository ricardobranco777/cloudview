"""
Instance class
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from libcloud.compute.types import NodeState, LibcloudError
from requests.exceptions import RequestException

from cloudview.singleton import Singleton2

STATES = [str(getattr(NodeState, _)) for _ in dir(NodeState) if _.isupper()]


@dataclass(kw_only=True)
class Instance:  # pylint: disable=too-many-instance-attributes
    """
    Instance class
    """

    provider: str
    cloud: str
    name: str
    id: str
    size: str
    time: str | datetime
    state: str
    location: str
    extra: dict

    # Allow access this object as a dictionary

    def __getitem__(self, item: str) -> Any:
        try:
            return getattr(self, item)
        except AttributeError as exc:
            raise KeyError(exc) from exc

    def __setitem__(self, item: str, value: Any) -> None:
        setattr(self, item, value)

    def __delitem__(self, item: str) -> None:
        try:
            delattr(self, item)
        except AttributeError as exc:
            raise KeyError(exc) from exc


class CSP(metaclass=Singleton2):
    """
    Cloud Service Provider class
    """

    def __init__(self, cloud: str = "") -> None:
        self.cloud = cloud or "_"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cloud='{self.cloud}')"

    def _get_instances(self) -> list[Instance]:
        raise NotImplementedError("CSP._get_instances needs to be overridden")

    def get_instances(self) -> list[Instance]:
        """
        Get instances
        """
        try:
            return self._get_instances()
        except (LibcloudError, RequestException) as exc:
            logging.error("%s: %s: %s", self.__class__.__name__, self.cloud, exc)
            return []
