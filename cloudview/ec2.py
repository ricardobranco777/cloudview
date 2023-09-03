"""
Reference:
https://libcloud.readthedocs.io/en/stable/compute/drivers/ec2.html
"""

import logging
import os
import concurrent.futures

from cachetools import cached, TTLCache
from libcloud.compute.base import Node, NodeDriver
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, LibcloudError, InvalidCredsError

from cloudview.instance import Instance, CSP, CACHED_SECONDS
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
            key_secret = (creds.pop("key"), creds.pop("secret"))
        except KeyError as exc:
            logging.error("EC2: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc
        cls = get_driver(Provider.EC2)
        self.regions = cls.list_regions()
        self._drivers: dict[str, NodeDriver] = {
            region: cls(*key_secret, region=region) for region in self.regions
        }

    def _list_instances_in_region(self, region: str) -> list[Instance]:
        try:
            return [
                self._node_to_instance(node, region)
                for node in self._drivers[region].list_nodes(ex_filters=None)
            ]
        except InvalidCredsError:
            pass
        return []

    def _get_instance(self, instance_id: str, params: dict) -> Instance:
        region = params["region"]
        node = self._drivers[region].list_nodes(ex_node_ids=[instance_id])[0]
        return self._node_to_instance(node, region)

    @cached(cache=TTLCache(maxsize=1, ttl=CACHED_SECONDS))
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

    def _node_to_instance(self, node: Node, region: str) -> Instance:
        return Instance(
            provider=Provider.EC2,
            cloud=self.cloud,
            name=node.extra["tags"].get("Name", node.name),
            id=node.id,
            size=node.extra["instance_type"],
            time=utc_date(node.extra["launch_time"]),
            state=node.state,
            location=node.extra["availability"],
            extra=node.extra,
            params={"region": region},
        )
