"""
Reference:
https://libcloud.readthedocs.io/en/stable/compute/drivers/ec2.html
"""

import logging
import os
import concurrent.futures

from libcloud.compute.base import Node, NodeDriver
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, LibcloudError, InvalidCredsError

from cloudview.instance import Instance, CSP
from cloudview.utils import utc_date


def get_creds() -> dict[str, str]:
    """
    Get credentials
    """
    creds: dict[str, str] = {}
    for key, env in (("key", "AWS_ACCESS_KEY_ID"), ("secret", "AWS_SECRET_ACCESS_KEY")):
        value = os.getenv(env)
        if value:
            creds |= {key: value}
    return creds


class EC2(CSP):  # pylint: disable=too-few-public-methods
    """
    Class for handling EC2 stuff
    """

    def __init__(self, cloud: str = "", **creds) -> None:
        super().__init__(cloud)
        creds = creds or get_creds()
        try:
            key_secret = (creds.pop("key"), creds.pop("secret"))
        except KeyError as exc:
            logging.error("EC2: %s: %s", self.cloud, exc)
            raise LibcloudError(f"{exc}") from exc
        cls = get_driver(Provider.EC2)
        self.regions = cls.list_regions()
        self._drivers: dict[str, NodeDriver] = {
            region: cls(*key_secret, region=region) for region in self.regions
        }

    def _list_instances_in_region(self, region: str) -> list[Instance]:
        try:
            return [
                self._node_to_instance(node)
                for node in self._drivers[region].list_nodes(ex_filters=None)
            ]
        except InvalidCredsError:
            pass
        return []

    def _get_instances(self) -> list[Instance]:
        instances = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(self.regions)
        ) as executor:
            future_to_region = {
                executor.submit(self._list_instances_in_region, region): region
                for region in self.regions
            }
            for future in concurrent.futures.as_completed(future_to_region):
                instances.extend(future.result())
        return instances

    def _node_to_instance(self, node: Node) -> Instance:
        return Instance(
            provider=Provider.EC2,
            cloud=self.cloud,
            name=node.extra["tags"].get("Name", node.name),
            id=str(node.id),
            size=node.extra["instance_type"],
            time=utc_date(node.extra["launch_time"]),
            state=node.state,
            location=node.extra["availability"],
            extra=node.extra,
        )
