#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Reference:
https://cloud.google.com/compute/docs/reference/rest/v1/instances/list
"""

import json
import os

from googleapiclient.discovery import build
from google.cloud import resource_manager
from providers.exceptions import SomeError


def get_project():
    """
    Get the project from the GCP credentials JSON file
    """
    try:
        with open(os.environ['GOOGLE_APPLICATION_CREDENTIALS']) as file:
            data = json.loads(file.read())
    except Exception as error:
        raise SomeError(error)
    return data['project_id']


class GCP:
    """
    Class for handling GCP stuff
    """
    def __init__(self, project=None):
        try:
            self.client = resource_manager.Client()
            self.compute = build('compute', 'v1')
        except Exception as error:
            raise SomeError(error)
        if project is None:
            self.project = get_project()
        else:
            self.project = project
        self.zones = self.get_zones(self.project)

    def get_projects(self):
        """
        Returns a list of projects
        """
        try:
            return [_.project_id for _ in self.client.list_projects()]
        except Exception as error:
            raise SomeError(error)

    def get_zones(self, project, filters="status: UP"):
        """
        Returns a list of available zones
        """
        items = []
        request = self.compute.zones().list(project=project, filter=filters)
        while request is not None:
            try:
                response = request.execute()
            except Exception as error:
                raise SomeError(error)
            if 'items' in response:
                items.extend(_['name'] for _ in response['items'])
            request = self.compute.zones().list_next(request, response)
        return items

    def get_instances(self, filters, orderBy=None):
        """
        Get GCP instances
        Only sorting by "name" or "creationTimestamp desc" is supported
        Specifying both a list filter and sort order is not currently supported
        """
        if filters is not None and orderBy is not None:
            raise ValueError("Specifying both a list filter and sort order is not currently supported")

        instances = []
        requests = {}
        responses = {}

        def callback(request_id, response, exception):
            if exception is not None:
                raise SomeError(exception)
            if 'items' in response:
                instances.extend(response['items'])
                if 'nextPageToken' in response:
                    retry_zones.append(request_id)
                    responses[request_id] = response

        retry_zones = self.zones
        # To support pagination on batch HTTP requests
        # we save the request & response of each zone
        while retry_zones:
            batch = self.compute.new_batch_http_request()
            for zone in retry_zones:
                if zone not in requests:
                    # Uncomment maxResults=1 to test pagination
                    requests[zone] = self.compute.instances().list(
                        project=self.project, zone=zone,
                        filter=filters, orderBy=orderBy)  # , maxResults=1)
                batch.add(requests[zone], callback=callback, request_id=zone)
            retry_zones.clear()
            try:
                batch.execute()
            except Exception as error:
                raise SomeError(error)
            for instance in instances:
                yield instance
            instances.clear()
            for zone in retry_zones:
                requests[zone] = self.compute.instances().list_next(
                    requests[zone], responses[zone])

    @staticmethod
    def get_tags(instance):
        """
        Returns a dictionary of tags
        """
        return instance['tags']

    @staticmethod
    def get_status(instance):
        """
        Returns the status of a VM instance
        provisioning | staging | running | stopping | stopped | suspending | suspended | terminated
        """
        return instance['status'].lower()
