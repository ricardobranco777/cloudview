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
            key_secret = (creds.pop("key"), creds.pop("secret"))
        except KeyError as exc:
            logging.error("EC2: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc
        cls = get_driver(Provider.EC2)
        self.regions = cls.list_regions()
        self._drivers: dict[str, NodeDriver] = {
            region: cls(*key_secret, region=region) for region in self.regions
        }

    def list_instances_in_region(self, region: str) -> list[Instance]:
        """
        List instances in region
        """
        try:
            return [
                self._node_to_instance(node, region)
                for node in self._drivers[region].list_nodes(ex_filters=None)
            ]
        except InvalidCredsError:
            pass
        except (LibcloudError, RequestException) as exc:
            logging.error("EC2: %s: %s", self.cloud, exception(exc))
        return []

    def _get_instance(self, identifier: str, params: dict) -> Instance | None:
        instance_id = identifier
        try:
            region = params["region"]
            node = self._drivers[region].list_nodes(ex_node_ids=[instance_id])[0]
        except (KeyError, TypeError, LibcloudError, RequestException) as exc:
            logging.error("EC2: %s: %s: %s", self.cloud, identifier, exception(exc))
            return None
        return self._node_to_instance(node, region)

    def _get_instances(self) -> list[Instance]:
        """
        Get EC2 instances
        """
        instances = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(self.regions)
        ) as executor:
            future_to_region = {
                executor.submit(self.list_instances_in_region, region): region
                for region in self.regions
            }
            for future in concurrent.futures.as_completed(future_to_region):
                # region = future_to_region[future]
                instances.extend(future.result())
        return instances

    def _node_to_instance(self, node: Node, region: str) -> Instance:
        """
        Node to Instance
        """
        return Instance(
            provider=Provider.EC2,
            cloud=self.cloud,
            name=node.name,
            id=node.id,
            size=node.extra["instance_type"],
            time=utc_date(node.extra["launch_time"]),
            state=node.state,
            location=node.extra["availability"],
            extra=node.extra,
            identifier=node.id,
            params={"region": region},
        )
