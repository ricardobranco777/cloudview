#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
References:
https://docs.microsoft.com/en-us/python/api/azure-mgmt-compute/azure.mgmt.compute.v2018_10_01.operations.virtualmachinesoperations?view=azure-python
"""

import re
import os

import concurrent.futures

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from msrestazure.azure_exceptions import CloudError
from requests.exceptions import RequestException

from cloudview.exceptions import FatalError
from cloudview.singleton import Singleton


def get_credentials():
    """
    Get credentials for Azure
    """
    try:
        subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
        credentials = ServicePrincipalCredentials(
            client_id=os.environ['AZURE_CLIENT_ID'],
            secret=os.environ['AZURE_CLIENT_SECRET'],
            tenant=os.environ['AZURE_TENANT_ID'])
        return credentials, subscription_id
    except (KeyError, CloudError, RequestException) as exc:
        FatalError("Azure", exc)


@Singleton
class Azure:
    """
    Class for handling Azure stuff
    """
    def __init__(self, api_version='2018-10-01'):
        credentials, subscription_id = get_credentials()
        try:
            self.compute = ComputeManagementClient(
                credentials, subscription_id, api_version=api_version)
        except (CloudError, RequestException) as exc:
            FatalError("Azure", exc)
        self._cache = None

    def _get_instance_view(self, instance):
        """
        Get instance view for more information
        """
        resource_group = re.search(
            r"/resourceGroups/([^/]+)/", instance.id).group(1)
        # https://github.com/Azure/azure-sdk-for-python/issues/573
        try:
            instance_view = self.compute.virtual_machines.instance_view(
                resource_group, instance.name)
        except (CloudError, RequestException) as exc:
            FatalError("Azure", exc)
        instance.instance_view = instance_view
        return instance.as_dict()

    def _get_instance_views(self, instances):
        """
        Threaded version to get all instance views using a pool of workers
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            yield from executor.map(self._get_instance_view, instances)

    @staticmethod
    def _get_date(instance):
        """
        Guess date for instance based on the OS disk
        """
        for disk in instance['instance_view']['disks']:
            if disk['name'] == instance['storage_profile']['os_disk']['name']:
                return disk['statuses'][0].get('time')
        return None

    @staticmethod
    def _get_status(instance):
        """
        Returns the status of the VM:
        starting | running | stopping | stopped | deallocating | deallocated
        """
        status = instance['instance_view']['statuses']
        if len(status) > 1:
            status = status[1]['code']
        else:
            status = status[0]['code']
        return status.rsplit('/', 1)[1]

    @staticmethod
    def get_tags(instance):
        """
        Returns a dictionary of tags
        """
        return instance['tags']

    def get_instances(self, filters=None):
        """
        Get Azure Compute instances
        """
        try:
            instances = self.compute.virtual_machines.list_all()
        except (CloudError, RequestException) as exc:
            FatalError("Azure", exc)
        # https://github.com/Azure/azure-sdk-for-python/issues/573
        instances = self._get_instance_views(instances)
        if filters is not None:
            instances = filter(filters.search, instances)
        instances = list(instances)
        for instance in instances:
            instance['date'] = self._get_date(instance)
            instance['status'] = self._get_status(instance)
        self._cache = instances
        return instances

    def get_instance(self, instance_id):
        """
        Return specific instance
        """
        if self._cache is None:
            self.get_instances()
        for instance in self._cache:
            if instance['vm_id'] == instance_id:
                return instance
        return None
