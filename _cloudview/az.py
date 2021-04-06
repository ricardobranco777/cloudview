#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
References:
https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines/instanceview
https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines/listall
"""

import re
import os

from concurrent.futures import ThreadPoolExecutor

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import AzureError
from msrestazure.azure_exceptions import CloudError
from requests.exceptions import RequestException

from _cloudview.exceptions import FatalError
from _cloudview.singleton import Singleton


def get_credentials():
    """
    Get credentials for Azure
    """
    try:
        subscription_id = os.getenv(
            'AZURE_SUBSCRIPTION_ID',
            os.getenv('ARM_SUBSCRIPTION_ID'))
        credentials = DefaultAzureCredential()
        return credentials, subscription_id
    except (KeyError, AzureError, CloudError, RequestException) as exc:
        FatalError("Azure", exc)
    return None


@Singleton
class Azure:
    """
    Class for handling Azure stuff
    """
    def __init__(self, api_version=None):
        credentials, subscription_id = get_credentials()
        try:
            self._client = ComputeManagementClient(
                credential=credentials,
                subscription_id=subscription_id,
                api_version=api_version)
        except (AzureError, CloudError, RequestException) as exc:
            FatalError("Azure", exc)
        self._cache = None

    def __del__(self):
        self._client.close()

    def _get_instance_view(self, instance):
        """
        Get instance view for more information
        """
        resource_group = re.search(
            r"/resourceGroups/([^/]+)/", instance.id).group(1)
        # https://github.com/Azure/azure-sdk-for-python/issues/573
        try:
            instance_view = self._client.virtual_machines.instance_view(
                resource_group, instance.name)
        except (AzureError, CloudError, RequestException) as exc:
            FatalError("Azure", exc)
        instance.instance_view = instance_view
        return instance.as_dict()

    def _get_instance_views(self, instances):
        """
        Threaded version to get all instance views using a pool of workers
        """
        with ThreadPoolExecutor() as executor:
            yield from executor.map(self._get_instance_view, instances)

    @staticmethod
    def get_date(instance):
        """
        Guess date for instance based on the OS disk
        """
        for disk in instance['instance_view']['disks']:
            if disk['name'] == instance['storage_profile']['os_disk']['name']:
                try:
                    return disk['statuses'][0]['time']
                except KeyError:
                    break
        return instance['instance_view']['statuses'][0].get('time')

    @staticmethod
    def get_status(instance):
        """
        Returns the power status (or the provisioning state) of the VM:
        https://docs.microsoft.com/en-us/azure/virtual-machines/windows/states-lifecycle
        starting | running | stopping | stopped | deallocating | deallocated
        """
        status = instance['instance_view']['statuses']
        if len(status) > 1:
            status = status[1]['display_status']
        else:
            status = status[0]['display_status']
        return status.split()[-1].lower()

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
            instances = self._client.virtual_machines.list_all()
        except (AzureError, CloudError, RequestException) as exc:
            FatalError("Azure", exc)
        # https://github.com/Azure/azure-sdk-for-python/issues/573
        instances = self._get_instance_views(instances)
        if filters is not None:
            instances = filter(filters.search, instances)
        instances = list(instances)
        self._cache = instances
        return instances

    def get_instance(self, instance_id, name=None, resource_group=None):
        """
        Return specific instance
        """
        if self._cache is None:
            if name is None or resource_group is None:
                self.get_instances()
            else:
                try:
                    return self._client.virtual_machines.get(
                        resource_group_name=resource_group,
                        vm_name=name, expand="instanceView").as_dict()
                except (AzureError, CloudError, RequestException) as exc:
                    FatalError("Azure", exc)
        for instance in self._cache:
            if instance['vm_id'] == instance_id:
                return instance
        return None
