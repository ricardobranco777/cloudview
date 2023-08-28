"""
References:
https://libcloud.readthedocs.io/en/stable/compute/drivers/openstack.html
https://docs.openstack.org/python-openstackclient/latest/cli/man/openstack.html
"""

import logging
import os
from functools import cached_property
from urllib.parse import urlparse
from typing import Optional

import libcloud.security
from libcloud.compute.base import NodeSize
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, LibcloudError
from requests.exceptions import RequestException
from cachetools import cached, TTLCache

from cloudview.instance import Instance, CSP
from cloudview.utils import utc_date, exception


libcloud.security.CA_CERTS_PATH = os.getenv("REQUESTS_CA_BUNDLE")


def get_creds() -> dict:
    """
    Get credentials
    """
    url = os.getenv("OS_AUTH_URL")
    if not url:
        return {}
    creds = {}
    for key, *env_vars in (
        ("key", "OS_USERNAME"),
        ("secret", "OS_PASSWORD"),
        ("ex_domain_name", "OS_USER_DOMAIN_NAME"),
        ("ex_tenant_name", "OS_PROJECT_NAME", "OS_TENANT_NAME"),
    ):
        for var in env_vars:
            value = os.getenv(var)
            if value:
                creds.update({key: value})
                break
    if not url.startswith(("https://", "http://")):
        url = f"https://{url}"
    url = urlparse(url)  # type: ignore
    auth_url = f"{url.scheme}://{url.netloc}"
    server = url.netloc.split(":")[0]
    base_url = f"{url.scheme}://{server}:8774/v2.1"
    creds.update(
        {
            "ex_force_auth_url": auth_url,
            "ex_force_base_url": base_url,
            "api_version": "2.2",
        }
    )
    return creds


class Openstack(CSP):
    """
    Class for handling Openstack stuff
    """

    def __init__(self, cloud: str = "", **creds):
        super().__init__(cloud)
        creds = creds or get_creds()
        try:
            self.key = creds.pop("key")
        except KeyError as exc:
            logging.error("Openstack: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc
        self.creds = creds
        self.options = {"ex_all_tenants": False}
        self._driver = None

    @cached_property
    def driver(self):
        """
        Get driver
        """
        if self._driver is None:
            cls = get_driver(Provider.OPENSTACK)
            try:
                self._driver = cls(self.key, **self.creds)
            except LibcloudError as exc:
                logging.error("Openstack: %s: %s", self.cloud, exception(exc))
                raise
            except RequestException as exc:
                logging.error("Openstack: %s: %s", self.cloud, exception(exc))
                raise LibcloudError(f"{exc}") from exc
        return self._driver

    def get_size(self, size_id: str) -> str:
        """
        Get size name by id
        """
        for size in self.get_sizes():
            if size.id == size_id:
                return size.name
        return "unknown"

    @cached(cache=TTLCache(maxsize=1, ttl=300))
    def get_sizes(self) -> list[NodeSize]:
        """
        Get sizes
        """
        try:
            return self.driver.list_sizes()
        except (LibcloudError, RequestException) as exc:
            logging.error("Openstack: %s: %s", self.cloud, exception(exc))
            raise

    def _get_instance(self, identifier: str, _: dict) -> Optional[Instance]:
        """
        Get instance
        """
        instance_id = identifier
        try:
            instance = self.driver.ex_get_node_details(instance_id)
        except (AttributeError, LibcloudError, RequestException) as exc:
            logging.error(
                "OpenStack: %s: %s: %s", self.cloud, identifier, exception(exc)
            )
            return None
        return Instance(extra=instance.extra)

    def _get_instances(self) -> list[Instance]:
        """
        Get Openstack instances
        """
        all_instances = []

        try:
            instances = self.driver.list_nodes(**self.options)
        except (LibcloudError, RequestException) as exc:
            logging.error("Openstack: %s: %s", self.cloud, exception(exc))
            return []

        for instance in instances:
            all_instances.append(
                Instance(
                    provider=Provider.OPENSTACK,
                    cloud=self.cloud,
                    name=instance.name,
                    id=instance.id,
                    size=self.get_size(instance.extra["flavorId"]),
                    time=utc_date(instance.extra["created"]),
                    state=instance.state,
                    location=instance.extra["availability_zone"],
                    extra=instance.extra,
                    identifier=instance.id,
                    params={},
                )
            )

        return all_instances
