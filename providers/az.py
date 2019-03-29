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

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient


def get_credentials():
    """
    Get credentials for Azure
    """
    subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
    credentials = ServicePrincipalCredentials(
        client_id=os.environ['AZURE_CLIENT_ID'],
        secret=os.environ['AZURE_CLIENT_SECRET'],
        tenant=os.environ['AZURE_TENANT_ID'])
    return credentials, subscription_id


class Azure:
    """
    Class for handling Azure stuff
    """
    def __init__(self, api_version='2018-10-01'):
        credentials, subscription_id = get_credentials()
        self.compute = ComputeManagementClient(
            credentials, subscription_id, api_version=api_version)

    def __del__(self):
        self.compute.close()

    def _get_instance_view(self, instance_id, instance_name):
        """
        Get instance view for more information
        """
        resource_group = re.search(
            r"/resourceGroups/([^/]+)/", instance_id).group(1)
        # https://github.com/Azure/azure-sdk-for-python/issues/573
        return self.compute.virtual_machines.instance_view(
            resource_group, instance_name)

    @staticmethod
    def _get_date(instance):
        """
        Guess date for instance based on the OS disk
        """
        for _, disk in enumerate(instance.instance_view.disks):
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
        return instance.tags

    def get_instances(self, filters=None):
        """
        Get Azure Compute instances
        """
        for instance in self.compute.virtual_machines.list_all():
            # https://github.com/Azure/azure-sdk-for-python/issues/573
            if instance.instance_view is None:
                instance.instance_view = self._get_instance_view(
                    instance.id, instance.name)
            setattr(instance, 'date', self._get_date(instance))
            setattr(instance, 'status', self._get_status(instance))
            if filters is not None and not filters.search(instance.as_dict()):
                continue
            yield instance
