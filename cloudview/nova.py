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

from novaclient import client

from cloudview.exceptions import FatalError
from cloudview.singleton import Singleton


@Singleton
class Nova:
    """
    Class for handling AWS stuff
    """
    def __init__(self, api_version=2.8, insecure=False):
        if insecure:
            # https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
            import logging
            logging.captureWarnings(True)
        try:
            self.client = client.Client(
                version=api_version,
                username=os.environ['OS_USERNAME'],
                password=os.environ['OS_PASSWORD'],
                project_id=os.environ.get(
                    'OS_PROJECT_ID',
                    os.environ.get('OS_TENANT_ID')),
                project_name=os.environ.get(
                    'OS_PROJECT_NAME',
                    os.environ.get('OS_TENANT_NAME')),
                project_domain_id=os.environ.get('OS_PROJECT_DOMAIN_ID', 'default'),
                region_name=os.environ.get('OS_REGION_NAME'),
                auth_url=os.environ['OS_AUTH_URL'],
                user_domain_name=os.environ.get('OS_USER_DOMAIN_NAME', 'Default'),
                cacert=os.environ.get('OS_CACERT'),
                insecure=insecure)
        except (Exception,) as exc:
            raise FatalError("Nova", exc)
        self._cache = None
        # Remove these variables from the environment
        for var in [_ for _ in os.environ if _.startswith('OS_')]:
            os.environ.unsetenv(var)

    def get_instances(self, filters=None):
        """
        Get Nova instances
        """
        if filters is None:
            filters = {}
        instances = []
        try:
            # https://developer.openstack.org/api-ref/compute/#list-servers
            for instance in self.client.servers.list(search_opts=filters):
                instances.append(instance.to_dict())
        except (Exception,) as exc:
            raise FatalError("Nova", exc)
        self._get_instance_types(instances)
        self._cache = instances
        return instances

    def get_instance(self, instance_id):
        """
        Return specific instance
        """
        if self._cache is None:
            self.get_instances()
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
            return self.client.flavors.get(flavor_id).name
        except (Exception,) as exc:
            raise FatalError("Nova", exc)

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
        Returns the status of the Nova instance: XXX
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
