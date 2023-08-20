"""
Reference:
https://libcloud.readthedocs.io/en/stable/compute/drivers/ec2.html
"""

import logging
import os
import concurrent.futures
from typing import Dict, List, Set

from cachetools import cached, TTLCache
from libcloud.compute.base import Node
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, LibcloudError, InvalidCredsError
from requests.exceptions import RequestException

from cloudview.instance import Instance, CSP
from cloudview.utils import utc_date, exception


def get_creds() -> Dict[str, str]:
    """
    Get credentials
    """
    creds = {}
    for key, env in (('key', "AWS_ACCESS_KEY_ID"), ('secret', "AWS_SECRET_ACCESS_KEY")):
        value = os.getenv(env)
        if value:
            creds.update({key: value})
    return creds


class EC2(CSP):
    """
    Class for handling EC2 stuff
    """
    def __init__(self, cloud: str = "", **creds):
        if hasattr(self, "cloud"):
            return
        super().__init__(cloud)
        creds = creds or get_creds()
        try:
            self.creds = (creds.pop('key'), creds.pop('secret'))
        except KeyError as exc:
            logging.error("EC2: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc
        cls = get_driver(Provider.EC2)
        self.driver = cls(*self.creds)
        try:
            self.list_regions()
        except (LibcloudError, RequestException) as exc:
            logging.error("EC2: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc

    @cached(cache=TTLCache(maxsize=1, ttl=300))
    def list_regions(self) -> Set[str]:
        """
        List regions
        """
        # NOTE: self.driver.list_regions() returns hard-coded shit
        return set(location.availability_zone.region_name for location in self.driver.list_locations())

    def list_instances_in_region(self, region: str) -> List[Node]:
        """
        List instance in region
        """
        cls = get_driver(Provider.EC2)
        try:
            driver = cls(*self.creds, region=region)
        except (LibcloudError, RequestException) as exc:
            logging.error("EC2: %s: %s", self.cloud, exception(exc))
            return []
        try:
            return driver.list_nodes(ex_filters=None)
        except InvalidCredsError:
            pass
        except (LibcloudError, RequestException) as exc:
            logging.error("EC2: %s: %s", self.cloud, exception(exc))
        return []

    def _get_instances(self) -> List[Instance]:
        """
        Get EC2 instances
        """
        all_instances = []

        try:
            regions = self.list_regions()
        except (LibcloudError, RequestException) as exc:
            logging.error("EC2: %s: %s", self.cloud, exception(exc))
            return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(regions)) as executor:
            future_to_region = {executor.submit(self.list_instances_in_region, region): region for region in regions}
            for future in concurrent.futures.as_completed(future_to_region):
                # region = future_to_region[future]
                instances = future.result()
                for instance in instances:
                    all_instances.append(
                        Instance(
                            provider="EC2",
                            cloud=self.cloud,
                            name=instance.name,
                            id=instance.id,
                            size=instance.extra['instance_type'],
                            time=utc_date(instance.extra['launch_time']),
                            state=instance.state,
                            location=instance.extra['availability'],
                            extra=instance.extra,
                        )
                    )

        return all_instances
