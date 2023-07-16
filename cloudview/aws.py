#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Reference:
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
"""

from boto3 import client
from botocore.exceptions import BotoCoreError, ClientError

from cloudview.errors import error, warning
from cloudview.singleton import Singleton


@Singleton
class AWS:
    """
    Class for handling AWS stuff
    """
    def __init__(self):
        try:
            self._client = client('ec2')
        except (BotoCoreError, ClientError) as exc:
            error("AWS", exc)

    @staticmethod
    def get_tags(instance):
        """
        Return a dictionary of tags
        """
        return {_['Key']: _['Value'] for _ in instance.get('Tags', {})}

    def get_instances(self, filters=None, jmespath_filter=None):
        """
        Get EC2 instances
        """
        filters = filters or []
        instances = []
        try:
            pages = self._client.get_paginator('describe_instances').paginate(
                Filters=filters)
        except (BotoCoreError, ClientError) as exc:
            error("AWS", exc)
        if jmespath_filter is not None:
            pages = pages.search(jmespath_filter)
        for page in pages:
            for item in page['Reservations']:
                instances.extend(item['Instances'])
        return instances

    def get_instance(self, instance_id):
        """
        Return specific instance
        """
        try:
            return self._client.describe_instances(
                InstanceIds=[instance_id])
        except (BotoCoreError, ClientError) as exc:
            warning("AWS", exc)
        return None

    @staticmethod
    def get_status(instance):
        """
        Returns the status of the EC2 instance:
        pending | running | stopping | stopped | shutting-down | terminated
        """
        return instance['State']['Name']
