"""
Reference:
https://libcloud.readthedocs.io/en/stable/compute/drivers/gce.html
"""

import json
import logging
import os
import concurrent.futures
from typing import Dict, List

from cachetools import cached, TTLCache
from libcloud.compute.base import Node
from libcloud.compute.drivers.gce import GCEZone
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, LibcloudError
from requests.exceptions import RequestException

from cloudview.instance import Instance, CSP
from cloudview.utils import utc_date, exception


def get_creds(creds: dict) -> Dict[str, str]:
    """
    Get credentials
    """
    creds_file = creds.get("key", os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
    if not creds_file or not os.path.isfile(creds_file) or all(v in creds for v in ("project", "user_id")):
        return creds
    with open(creds_file, encoding="utf-8") as file:
        data = json.loads(file.read())
    return {
        "key": creds_file,
        "project": data['project_id'],
        "user_id": data['client_email'],
    }


class GCE(CSP):
    """
    Class for handling GCE stuff
    """
    def __init__(self, cloud: str = "", **creds):
        if hasattr(self, "cloud"):
            return
        super().__init__(cloud)
        try:
            creds = get_creds(creds)
            self.user_id = creds.pop('user_id')
        except (KeyError, OSError, json.decoder.JSONDecodeError) as exc:
            logging.error("GCE: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc
        self.creds = creds
        cls = get_driver(Provider.GCE)
        try:
            self.driver = cls(self.user_id, **self.creds)
            self.list_zones()
        except (LibcloudError, RequestException) as exc:
            logging.error("GCE: %s: %s", self.cloud, exception(exc))
            raise LibcloudError(f"{exc}") from exc

    @cached(cache=TTLCache(maxsize=1, ttl=300))
    def list_zones(self) -> List[GCEZone]:
        """
        List zones
        """
        return self.driver.ex_list_zones()

    def list_instances_in_zone(self, zone: GCEZone) -> List[Node]:
        """
        List instances in zone
        """
        if zone.status != "UP":
            logging.debug("GCE: %s status is %s", zone.name, zone.status)
            return []
        cls = get_driver(Provider.GCE)
        try:
            driver = cls(self.user_id, **self.creds)
            return driver.list_nodes(ex_zone=zone)
        except (LibcloudError, RequestException) as exc:
            logging.error("GCE: %s: %s", self.cloud, exception(exc))
            return []

    def _get_instances(self) -> List[Instance]:
        """
        Get GCE instances
        """
        all_instances = []

        try:
            zones = self.list_zones()
        except (LibcloudError, RequestException) as exc:
            logging.error("GCE: %s: %s", self.cloud, exception(exc))
            return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(zones)) as executor:
            future_to_zone = {executor.submit(self.list_instances_in_zone, zone): zone for zone in zones}
            for future in concurrent.futures.as_completed(future_to_zone):
                # zone = future_to_zone[future]
                instances = future.result()
                for instance in instances:
                    all_instances.append(
                        Instance(
                            provider="GCE",
                            cloud=self.cloud,
                            name=instance.name,
                            id=instance.id,
                            size=instance.extra['machineType'].split('/')[-1],
                            time=utc_date(instance.extra['creationTimestamp']),
                            state=instance.state,
                            location=instance.extra['zone'].name,
                            extra=instance.extra,
                        )
                    )

        return all_instances
