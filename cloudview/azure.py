"""
Reference:
https://libcloud.readthedocs.io/en/stable/compute/drivers/azure_arm.html
"""

import logging
import os
from functools import cached_property

from libcloud.compute.base import Node, NodeDriver
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, LibcloudError
from requests.exceptions import RequestException

from cloudview.instance import Instance, CSP
from cloudview.utils import utc_date


def get_creds() -> dict[str, str]:
    """
    Get credentials
    """
    creds: dict[str, str] = {}
    for key, *env_vars in (
        ("key", "AZURE_CLIENT_ID", "ARM_CLIENT_ID"),
        ("secret", "AZURE_CLIENT_SECRET", "ARM_CLIENT_SECRET"),
        ("tenant_id", "AZURE_TENANT_ID", "ARM_TENANT_ID"),
        ("subscription_id", "AZURE_SUBSCRIPTION_ID", "ARM_SUBSCRIPTION_ID"),
    ):
        for var in env_vars:
            value = os.getenv(var)
            if value:
                creds |= {key: value}
                break
    return creds


class Azure(CSP):
    """
    Class for handling Azure stuff
    """

    def __init__(self, cloud: str = "", **creds) -> None:
        super().__init__(cloud)
        creds = creds or get_creds()
        try:
            self._creds = (
                creds.pop("tenant_id"),
                creds.pop("subscription_id"),
                creds.pop("key"),
                creds.pop("secret"),
            )
        except KeyError as exc:
            logging.error("Azure: %s: %s", self.cloud, exc)
            raise LibcloudError(f"{exc}") from exc
        self.options = {
            "ex_resource_group": None,
            "ex_fetch_nic": False,
            "ex_fetch_power_state": False,
        }
        self._driver: NodeDriver | None = None

    @cached_property
    def driver(self) -> NodeDriver:
        """
        Get driver
        """
        if self._driver is None:
            cls = get_driver(Provider.AZURE_ARM)
            try:
                self._driver = cls(*self._creds, **self.options)
            except RequestException as exc:
                logging.error("Azure: %s: %s", self.cloud, exc)
                raise LibcloudError(f"{exc}") from exc
        return self._driver

    def _get_instances(self) -> list[Instance]:
        return [self._node_to_instance(node) for node in self.driver.list_nodes()]

    def _node_to_instance(self, node: Node) -> Instance:
        return Instance(
            provider=Provider.AZURE_ARM,
            cloud=self.cloud,
            name=node.name,
            id=node.extra["properties"]["vmId"],
            size=node.extra["properties"]["hardwareProfile"]["vmSize"],
            time=utc_date(node.extra["properties"]["timeCreated"]),
            state=node.state,
            location=node.extra["location"],
            extra=node.extra,
        )
