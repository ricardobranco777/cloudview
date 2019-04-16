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
from googleapiclient.errors import Error as GoogleError, HttpError
from google.cloud import resource_manager
from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError

from .exceptions import FatalError, WarningError
from .singleton import Singleton


def get_project():
    """
    Get the project from the GCP credentials JSON file
    """
    try:
        with open(os.environ['GOOGLE_APPLICATION_CREDENTIALS']) as file:
            data = json.loads(file.read())
        return data['project_id']
    except (KeyError, OSError) as exc:
        FatalError("GCP", exc)


@Singleton
class GCP:
    """
    Class for handling GCP stuff
    """
    def __init__(self, project=None):
        try:
            self.client = resource_manager.Client()
        except (GoogleAuthError, GoogleAPIError) as exc:
            FatalError("GCP", exc)
        try:
            self.compute = build('compute', 'v1')
        except (GoogleAuthError, GoogleError) as exc:
            FatalError("GCP", exc)
        if project is None:
            self.project = get_project()
        else:
            self.project = project
        self._cache = None

    def get_projects(self):
        """
        Returns a list of projects
        """
        try:
            return [_.project_id for _ in self.client.list_projects()]
        except (GoogleAuthError, GoogleAPIError) as exc:
            FatalError("GCP", exc)

    # MAYBE use TTLCache
    def get_zones(self, project=None, filters="status: UP"):
        """
        Returns a list of available zones
        """
        if project is None:
            project = self.project
        items = []
        request = self.compute.zones().list(project=project, filter=filters)
        while request is not None:
            try:
                response = request.execute()
            except (GoogleAuthError, GoogleError) as exc:
                FatalError("GCP", exc)
            if 'items' in response:
                items.extend(_['name'] for _ in response['items'])
            request = self.compute.zones().list_next(request, response)
        return items

    def get_instances(self, filters=None, orderBy=None):
        """
        Get GCP instances
        Only sorting by "name" or "creationTimestamp desc" is supported
        Specifying both a list filter and sort order is not currently supported
        """
        if filters is not None and orderBy is not None:
            raise FatalError(
                "Specifying both a list filter and sort order is not currently supported",
                ValueError)

        instances = []
        requests = {}
        responses = {}

        def callback(request_id, response, exception):
            if exception is not None:
                # Handle some GCP errors with problematic zones
                if isinstance(exception, HttpError):
                    # pylint: disable=protected-access
                    reason = exception._get_reason()
                    if reason.startswith("Invalid value for field 'zone'"):
                        WarningError("GCP", exception)
                        return
                FatalError("GCP", exception)
            if 'items' in response:
                instances.extend(response['items'])
                if 'nextPageToken' in response:
                    retry_zones.append(request_id)
                    responses[request_id] = response

        retry_zones = self.get_zones()
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
            except (GoogleAuthError, GoogleError) as exc:
                FatalError("GCP", exc)
            for zone in retry_zones:
                requests[zone] = self.compute.instances().list_next(
                    requests[zone], responses[zone])
        self._cache = instances
        return instances

    def get_instance(self, instance_id):
        """
        Get specific instance
        """
        if self._cache is None:
            self.get_instances()
        for instance in self._cache:
            if instance['id'] == instance_id:
                return instance
        return None

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
        provisioning | staging | running | stopping |
        stopped | suspending | suspended | terminated
        """
        return instance['status'].lower()
