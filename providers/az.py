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
from .exceptions import FatalError
from .singleton import Singleton


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

    def _get_instance_view(self, instance):
        """
        Get instance view for more information
        """
        resource_group = re.search(
            r"/resourceGroups/([^/]+)/", instance.id).group(1)
        # https://github.com/Azure/azure-sdk-for-python/issues/573
        try:
            return self.compute.virtual_machines.instance_view(
                resource_group, instance.name)
        except (CloudError, RequestException) as exc:
            FatalError("Azure", exc)

    def _get_instance_views(self, instances):
        """
        Threaded version to get all instance views using a pool of workers
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Mark each future with its instance
            future_to_instance = {
                executor.submit(self._get_instance_view, instance):
                instance for instance in instances
            }
            for future in concurrent.futures.as_completed(future_to_instance):
                instance = future_to_instance[future]
                try:
                    instance.instance_view = future.result()
                except (CloudError, RequestException) as exc:
                    FatalError("Azure", exc)

    @staticmethod
    def _get_date(instance):
        """
        Guess date for instance based on the OS disk
        """
        for disk in instance.instance_view.disks:
            if disk.name == instance.storage_profile.os_disk.name:
                return disk.statuses[0].time
        return None

    @staticmethod
    def _get_status(instance):
        """
        Returns the status of the VM:
        starting | running | stopping | stopped | deallocating | deallocated
        """
        status = instance.instance_view.statuses
        if len(status) > 1:
            status = status[1].code
        else:
            status = status[0].code
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
            instances = list(self.compute.virtual_machines.list_all())
        except (CloudError, RequestException) as exc:
            FatalError("Azure", exc)
        # https://github.com/Azure/azure-sdk-for-python/issues/573
        self._get_instance_views(instances)
        for instance in instances:
            date = self._get_date(instance)
            status = self._get_status(instance)
            instance = instance.as_dict()
            instance['date'] = date
            instance['status'] = status
            if filters is not None and not filters.search(instance):
                continue
            yield instance
