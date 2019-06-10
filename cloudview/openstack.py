#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Reference:
https://developer.openstack.org/api-ref/compute/
"""

import os

import concurrent.futures

from functools import lru_cache

import openstack.cloud
from openstack.exceptions import OpenStackCloudException

from cloudview.exceptions import FatalError
from cloudview.singleton import Singleton2


@Singleton2
class Openstack:
    """
    Class for handling AWS stuff
    """
    def __init__(self, cloud=None, insecure=False):
        if insecure:
            # https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
            import logging
            logging.captureWarnings(True)
        try:
            self._client = openstack.connect(
                cloud=cloud, insecure=insecure)
        except OpenStackCloudException as exc:
            raise FatalError("Openstack", exc)
        self._cache = None
        # Remove these variables from the environment
        for var in [_ for _ in os.environ if _.startswith('OS_')]:
            os.environ.unsetenv(var)

    def get_instances(self, filters=None):
        """
        Get Openstack instances
        """
        if filters is None:
            filters = {}
        try:
            # https://developer.openstack.org/api-ref/compute/#list-servers
            instances = [_ for _ in self._client.list_servers(filters=filters)]
        except OpenStackCloudException as exc:
            raise FatalError("Openstack", exc)
        self._get_instance_types(instances)
        self._cache = instances
        return instances

    def get_instance(self, instance_id):
        """
        Return specific instance
        """
        if self._cache is None:
            try:
                return self._client.get_server_by_id(instance_id)
            except OpenStackCloudException as exc:
                raise FatalError("Openstack", exc)
        else:
            for instance in self._cache:
                if instance['id'] == instance_id:
                    return instance
        return None

    @lru_cache(maxsize=None)
    def get_instance_type(self, flavor_id):
        """
        Return instance type
        """
        try:
            return self._client.get_flavor_by_id(flavor_id).name
        except OpenStackCloudException as exc:
            raise FatalError("Openstack", exc)

    def _get_instance_types(self, instances):
        """
        Threaded version to get all instance types using a pool of workers
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(
                self.get_instance_type,
                {_['flavor']['id'] for _ in instances})

    @staticmethod
    def get_status(instance):
        """
        Returns the status of the Openstack instance
        """
        return instance['OS-EXT-STS:vm_state']

    @staticmethod
    def get_tags(instance):
        """
        Return a dictionary of tags
        """
        if 'tags' in instance:
            return dict.fromkeys(instance['tags'])
        return {}
