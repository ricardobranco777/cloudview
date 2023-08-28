"""
Reference:
https://libcloud.readthedocs.io/en/stable/compute/drivers/ec2.html
"""

import logging
import os
import concurrent.futures
from typing import Optional

from libcloud.compute.base import Node
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, LibcloudError, InvalidCredsError
from requests.exceptions import RequestException

from cloudview.instance import Instance, CSP
from cloudview.utils import utc_date, exception


def get_creds() -> dict[str, str]:
    """
    Get credentials
    """
    creds = {}
    for key, env in (("key", "AWS_ACCESS_KEY_ID"), ("secret", "AWS_SECRET_ACCESS_KEY")):
        value = os.getenv(env)
        if value:
            creds.update({key: value})
    return creds


class EC2(CSP):
    """
    Class for handling EC2 stuff
    """

    def __init__(self, cloud: str = "", **creds):
        super().__init__(cloud)
        creds = creds or get_creds()
        try:
            self.creds = (creds.pop("key"), creds.pop("secret"))
        except KeyError as exc:
            logging.error("EC2: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc
        cls = get_driver(Provider.EC2)
        self.regions = cls.list_regions()
        self._drivers = {
            region: cls(*self.creds, region=region) for region in self.regions
        }

    def list_instances_in_region(self, region: str) -> list[Node]:
        """
        List instance in region
        """
        try:
            return self._drivers[region].list_nodes(ex_filters=None)
        except InvalidCredsError:
            pass
        except (LibcloudError, RequestException) as exc:
            logging.error("EC2: %s: %s", self.cloud, exception(exc))
        return []

    def _get_instance(self, identifier: str, params: dict) -> Optional[Instance]:
        instance_id = identifier
        try:
            region = params["region"]
            instance = self._drivers[region].list_nodes(ex_node_ids=[instance_id])[0]
        except (KeyError, TypeError, LibcloudError, RequestException) as exc:
            logging.error("EC2: %s: %s: %s", self.cloud, identifier, exception(exc))
            return None
        return Instance(extra=instance.extra)

    def _get_instances(self) -> list[Instance]:
        """
        Get EC2 instances
        """
        all_instances = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(self.regions)
        ) as executor:
            future_to_region = {
                executor.submit(self.list_instances_in_region, region): region
                for region in self.regions
            }
            for future in concurrent.futures.as_completed(future_to_region):
                region = future_to_region[future]
                instances = future.result()
                for instance in instances:
                    all_instances.append(
                        Instance(
                            provider=Provider.EC2,
                            cloud=self.cloud,
                            name=instance.name,
                            id=instance.id,
                            size=instance.extra["instance_type"],
                            time=utc_date(instance.extra["launch_time"]),
                            state=instance.state,
                            location=instance.extra["availability"],
                            extra=instance.extra,
                            identifier=instance.id,
                            params={"region": region},
                        )
                    )
        return all_instances
