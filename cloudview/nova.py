#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Reference:
https://developer.openstack.org/api-ref/compute/
"""

import os

from novaclient import client

from cloudview.exceptions import FatalError
from cloudview.singleton import Singleton


@Singleton
class Nova:
    """
    Class for handling AWS stuff
    """
    def __init__(self, api_version=2.8, insecure=True):
        if insecure:
            # https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
            import logging
            logging.captureWarnings(True)
        try:
            self.client = client.Client(
                version=api_version,
                username=os.environ['OS_USERNAME'],
                password=os.environ['OS_PASSWORD'],
                project_id=os.environ['OS_PROJECT_ID'],
                auth_url=os.environ['OS_AUTH_URL'],
                user_domain_name=os.environ['OS_USER_DOMAIN_NAME'],
                insecure=insecure)
        except (KeyError,) as exc:
            raise FatalError("Nova", exc)
        self._cache = None

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

    def get_instance_type(self, instance):
        """
        Return instance type
        """
        return self.client.flavors.get(instance['flavor']['id']).name

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
