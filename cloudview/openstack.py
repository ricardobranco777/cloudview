"""
References:
https://libcloud.readthedocs.io/en/stable/compute/drivers/openstack.html
https://docs.openstack.org/python-openstackclient/latest/cli/man/openstack.html
"""

import logging
import os
from urllib.parse import urlparse
from typing import List

import libcloud.security
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, LibcloudError
from requests.exceptions import RequestException

from cloudview.instance import Instance, CSP
from cloudview.utils import utc_date, exception


libcloud.security.CA_CERTS_PATH = os.getenv('REQUESTS_CA_BUNDLE')


def get_creds() -> dict:
    """
    Get credentials
    """
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
    url = os.getenv("OS_AUTH_URL")
    if not url:
        return creds
    if not url.startswith(("https://", "http://")):
        url = f"https://{url}"
    url = urlparse(url)  # type: ignore
    auth_url = f"{url.scheme}://{url.netloc}"
    server = url.netloc.split(':')[0]
    base_url = f"{url.scheme}://{server}:8774/v2.1"
    creds.update({
        "ex_force_auth_url": auth_url,
        "ex_force_base_url": base_url,
        "api_version": "2.2",
    })
    return creds


class Openstack(CSP):
    """
    Class for handling Openstack stuff
    """
    def __init__(self, cloud: str = "", **creds):
        if hasattr(self, "cloud"):
            return
        super().__init__(cloud)
        creds = creds or get_creds()
        try:
            key = creds.pop('key')
        except KeyError as exc:
            logging.error("Openstack: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc
        cls = get_driver(Provider.OPENSTACK)
        try:
            self.driver = cls(key, **creds)
            self.sizes = self.driver.list_sizes()
        except LibcloudError as exc:
            logging.error("Openstack: %s: %s", self.cloud, exception(exc))
            raise
        except RequestException as exc:
            logging.error("Openstack: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc

    def get_size(self, id_: str) -> str:
        """
        Get size name by id
        """
        for size in self.sizes:
            if size.id == id_:
                return size.name
        return "unknown"

    def _get_instances(self) -> List[Instance]:
        """
        Get Openstack instances
        """
        all_instances = []

        try:
            instances = self.driver.list_nodes(ex_all_tenants=False)
        except LibcloudError as exc:
            logging.error("Openstack: %s: %s", self.cloud, exception(exc))
            return []

        for instance in instances:
            all_instances.append(
                Instance(
                    provider="Openstack",
                    cloud=self.cloud,
                    name=instance.name,
                    id=instance.id,
                    size=self.get_size(instance.extra['flavorId']),
                    time=utc_date(instance.extra['created']),
                    state=instance.state,
                    location=instance.extra['availability_zone'],
                    extra=instance.extra,
                )
            )

        return all_instances
