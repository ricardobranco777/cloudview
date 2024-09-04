"""
Instance class
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from libcloud.compute.types import NodeState, LibcloudError
from requests.exceptions import RequestException

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


class CSP:
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
