#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Reference:
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
"""

from boto3 import client as boto3_client
from botocore.exceptions import BotoCoreError, ClientError

from cloudview.exceptions import FatalError, WarningError
from cloudview.singleton import Singleton


@Singleton
class AWS:
    """
    Class for handling AWS stuff
    """
    def __init__(self):
        try:
            self.client = boto3_client('ec2')
        except (BotoCoreError, ClientError) as exc:
            raise FatalError("AWS", exc)
        self._cache = None

    @staticmethod
    def get_tags(instance):
        """
        Return a dictionary of tags
        """
        return {_['Key']: _['Value'] for _ in instance.get('Tags', {})}

    def get_instances(self, filters=None):
        """
        Get EC2 instances
        """
        if filters is None:
            filters = []
        instances = []
        try:
            pages = self.client.get_paginator('describe_instances').paginate(
                Filters=filters)
            # TODO: Use JMESPath for client-side filtering using pages.search()
        except (BotoCoreError, ClientError) as exc:
            raise FatalError("AWS", exc)
        for page in pages:
            for item in page['Reservations']:
                instances.extend(item['Instances'])
        self._cache = instances
        return instances

    def get_instance(self, instance_id):
        """
        Return specific instance
        """
        if self._cache is None:
            try:
                return self.client.describe_instances(InstanceIds=[instance_id])
            except (BotoCoreError, ClientError) as exc:
                raise WarningError("AWS", exc)
        else:
            for instance in self._cache:
                if instance['InstanceId'] == instance_id:
                    return instance
        return None

    @staticmethod
    def get_status(instance):
        """
        Returns the status of the EC2 instance:
        pending | running | stopping | stopped | shutting-down | terminated
        """
        return instance['State']['Name']
