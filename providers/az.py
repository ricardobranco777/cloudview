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
from providers.exceptions import SomeError


def get_credentials():
    """
    Get credentials for Azure
    """
    try:
        subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
        credentials = ServicePrincipalCredentials(
            client_id=os.environ['AZURE_CLIENT_ID'],
            secret=os.environ['AZURE_CLIENT_SECRET'],
            tenant=os.environ['AZURE_TENANT_ID']
        )
        return credentials, subscription_id
    except Exception as error:
        raise SomeError(error)


class Azure:
    """
    Class for handling Azure stuff
    """
    def __init__(self, api_version='2018-10-01'):
        credentials, subscription_id = get_credentials()
        self.compute = ComputeManagementClient(
            credentials, subscription_id, api_version=api_version)

    def _get_instance_view(self, instance_id, instance_name):
        """
        Get instance view for more information
        """
        resource_group = re.search(
            r"/resourceGroups/([^/]+)/", instance_id).group(1)
        try:
            # https://github.com/Azure/azure-sdk-for-python/issues/573
            return self.compute.virtual_machines.instance_view(
                resource_group, instance_name)
        except Exception as error:
            raise SomeError(error)

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
            status = status[1].display_status
        else:
            status = status[0].display_status
        if status.startswith("VM "):
            return status[3:]
        return status

    @staticmethod
    def get_tags(instance):
        """
        Returns a dictionary of tags
        """
        return instance.tags

    def get_instances(self, filter_instance=None, filter_instance_view=None):
        """
        Get Azure Compute instances
        Reference:
        https://docs.microsoft.com/en-us/python/azure/python-sdk-azure-operation-config?view=azure-python
        """
        try:
            for instance in self.compute.virtual_machines.list_all():
                # https://github.com/Azure/azure-sdk-for-python/issues/573
                if instance.instance_view is None:
                    instance.instance_view = self._get_instance_view(
                        instance.id, instance.name)
                setattr(instance, 'date', self._get_date(instance))
                setattr(instance, 'status', self._get_status(instance))
                if (filter_instance is not None and not
                        filter_instance.search(instance.as_dict())):
                    continue
                if (filter_instance_view is not None and not
                        filter_instance_view.search(
                            instance.instance_view.as_dict())):
                    continue
                yield instance
        except Exception as error:
            raise SomeError(error)
