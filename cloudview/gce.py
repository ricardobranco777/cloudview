"""
Reference:
https://libcloud.readthedocs.io/en/stable/compute/drivers/gce.html
"""

import json
import logging
import os
import concurrent.futures
from functools import cached_property

from cachetools import cached, TTLCache
from libcloud.compute.base import Node, NodeDriver
from libcloud.compute.drivers.gce import GCEZone
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, LibcloudError
from requests.exceptions import RequestException

from cloudview.instance import Instance, CSP, CACHED_SECONDS
from cloudview.utils import utc_date, exception, read_file


def get_creds(creds: dict) -> dict[str, str]:
    """
    Get credentials
    """
    creds_file = creds.get("key", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    if (
        not creds_file
        or not os.path.isfile(creds_file)
        or all(v in creds for v in ("project", "user_id"))
    ):
        return creds
    data = json.loads(read_file(creds_file))
    return {
        "key": creds_file,
        "project": data["project_id"],
        "user_id": data["client_email"],
    }


class GCE(CSP):
    """
    Class for handling GCE stuff
    """

    def __init__(self, cloud: str = "", **creds):
        super().__init__(cloud)
        try:
            creds = get_creds(creds)
            self.user_id = creds.pop("user_id")
        except (KeyError, OSError, json.decoder.JSONDecodeError) as exc:
            logging.error("GCE: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc
        self._creds = creds
        self._driver: NodeDriver | None = None

    @cached_property
    def driver(self) -> NodeDriver:
        """
        Get driver
        """
        if self._driver is None:
            cls = get_driver(Provider.GCE)
            try:
                self._driver = cls(self.user_id, **self._creds)
            except (LibcloudError, RequestException) as exc:
                logging.error("GCE: %s: %s", self.cloud, exception(exc))
                raise LibcloudError(f"{exc}") from exc
        return self._driver

    def _list_instances_in_zone(self, zone: GCEZone) -> list[Instance]:
        if zone.status != "UP":
            logging.debug("GCE: %s status is %s", zone.name, zone.status)
            return []
        try:
            return [
                self._node_to_instance(node)
                for node in self.driver.list_nodes(ex_zone=zone)
            ]
        except (LibcloudError, RequestException) as exc:
            logging.error("GCE: %s: %s", self.cloud, exception(exc))
            return []

    def _get_instance(self, identifier: str, params: dict) -> Instance:
        node = self.driver.ex_get_node(params["name"], zone=params["zone"])
        return self._node_to_instance(node)

    @cached(cache=TTLCache(maxsize=1, ttl=CACHED_SECONDS))
    def _get_instances(self) -> list[Instance]:
        zones = self.driver.ex_list_zones()
        instances = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(zones)) as executor:
            future_to_zone = {
                executor.submit(self._list_instances_in_zone, zone): zone
                for zone in zones
            }
            for future in concurrent.futures.as_completed(future_to_zone):
                instances.extend(future.result())
        return instances

    def _node_to_instance(self, node: Node) -> Instance:
        return Instance(
            provider=Provider.GCE,
            cloud=self.cloud,
            name=node.name,
            id=node.id,
            size=node.extra["machineType"].split("/")[-1],
            time=utc_date(node.extra["creationTimestamp"]),
            state=node.state,
            location=node.extra["zone"].name,
            extra=node.extra,
            identifier=node.name,
            params={
                "name": node.name,
                "zone": node.extra["zone"].name,
            },
        )
