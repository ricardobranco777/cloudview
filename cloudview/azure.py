"""
Reference:
https://libcloud.readthedocs.io/en/stable/compute/drivers/azure_arm.html
"""

import logging
import os
from typing import Dict, List

from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, LibcloudError
from requests.exceptions import RequestException

from cloudview.instance import Instance, CSP
from cloudview.utils import utc_date, exception


def get_creds() -> Dict[str, str]:
    """
    Get credentials
    """
    creds = {}
    for key, *env_vars in (
        ('key', "AZURE_CLIENT_ID", "ARM_CLIENT_ID"),
        ('secret', "AZURE_CLIENT_SECRET", "ARM_CLIENT_SECRET"),
        ('tenant_id', "AZURE_TENANT_ID", "ARM_TENANT_ID"),
        ('subscription_id', "AZURE_SUBSCRIPTION_ID", "ARM_SUBSCRIPTION_ID"),
    ):
        for var in env_vars:
            value = os.getenv(var)
            if value:
                creds.update({key: value})
                break
    return creds


class Azure(CSP):
    """
    Class for handling Azure stuff
    """
    def __init__(self, cloud: str = "", **creds):
        if hasattr(self, "cloud"):
            return
        super().__init__(cloud)
        creds = creds or get_creds()
        try:
            self.creds = (creds.pop('tenant_id'), creds.pop('subscription_id'), creds.pop('key'), creds.pop('secret'))
        except KeyError as exc:
            logging.error("Azure: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc
        cls = get_driver(Provider.AZURE_ARM)
        try:
            self.driver = cls(*self.creds, ex_resource_group=None, ex_fetch_nic=False, ex_fetch_power_state=True)
        except RequestException as exc:
            logging.error("Azure: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc

    def _get_instances(self) -> List[Instance]:
        """
        Get Azure instances
        """
        all_instances = []

        try:
            instances = self.driver.list_nodes()
        except (AttributeError, LibcloudError, RequestException) as exc:
            logging.error("Azure: %s: %s", self.cloud, exception(exc))
            return []

        for instance in instances:
            all_instances.append(
                Instance(
                    provider="Azure",
                    cloud=self.cloud,
                    name=instance.name,
                    id=instance.extra['properties']['vmId'],
                    size=instance.extra['properties']['hardwareProfile']['vmSize'],
                    time=utc_date(instance.extra['properties']['timeCreated']),
                    state=instance.state,
                    location=instance.extra['location'],
                    extra=instance.extra,
                )
            )

        return all_instances
