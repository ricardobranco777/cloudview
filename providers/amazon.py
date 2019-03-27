#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Reference:
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
"""

from boto3 import client as boto3_client
from providers.exceptions import SomeError


class AWS:
    """
    Class for handling AWS stuff
    """
    def __init__(self):
        try:
            self.client = boto3_client('ec2')
        except Exception as error:
            raise SomeError(error)

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
        try:
            paginator = self.client.get_paginator('describe_instances')
            for page in paginator.paginate(Filters=filters):
                for item in page['Reservations']:
                    for instance in item['Instances']:
                        yield instance
        except Exception as error:
            raise SomeError(error)

    @staticmethod
    def get_status(instance):
        """
        Returns the status of the EC2 instance:
        pending | running | stopping | stopped | shutting-down | terminated
        """
        return instance['State']['Name']
