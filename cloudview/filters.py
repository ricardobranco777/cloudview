"""
Filter by status
"""

from itertools import groupby
from operator import itemgetter

import jmespath
from jmespath.exceptions import JMESPathError

from .exceptions import FatalError


def filters_aws(filter_aws, status):
    """
    Filters for AWS
    """
    filters = []
    # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html
    if status in ('running', 'stopped'):
        # Consider an instance "running" if not stopped or terminated
        # and "stopped" if not pending or running, hence the overlap
        if status == "running":
            statuses = 'pending running stopping shutting-down'.split()
        else:
            statuses = 'stopping stopped shutting-down terminated'.split()
        filters = [['instance-state-name', _] for _ in statuses]
    # If instance-state-name was specified in the filter, use it instead
    if filter_aws:
        if 'instance-state-name' in {_[0] for _ in filter_aws}:
            filters = filter_aws
        else:
            filters.extend(filter_aws)
    # Compile filter using 'Name' & 'Values'
    filters = [
        {'Name': name, 'Values': [v for _, v in values]}
        for name, values in groupby(
            sorted(filters, key=itemgetter(0)), itemgetter(0))
    ]
    return filters


def filters_azure(filter_azure, status):
    """
    Filters for Azure
    """
    filters = ""
    # https://docs.microsoft.com/en-us/azure/virtual-machines/windows/states-lifecycle
    if status in ('running', 'stopped'):
        # Consider an instance "running" if not stopped / deallocated
        # and "stopped" if not starting or running, hence the overlap
        if status == "running":
            statuses = 'starting running stopping'
        else:
            statuses = 'stopping stopped deallocating deallocated'
        filters = " || ".join(
            f"instance_view.statuses[1].code == 'PowerState/{status}'"
            for status in statuses.split())
    # If status was specified in the filter, use it instead
    if filter_azure:
        if "instance_view.statuses" in filter_azure or not filters:
            filters = filter_azure
        else:
            filters += f" && ({filter_azure})"
    if filters:
        try:
            filters = jmespath.compile(filters)
        except JMESPathError as exc:
            FatalError("Azure", exc)
    return filters


def filters_gcp(filter_gcp, status):
    """
    Filters for GCP
    """
    filters = ""
    # https://cloud.google.com/compute/docs/instances/instance-life-cycle
    # NOTE: The above list is incomplete. The API returns more statuses
    if status in ('running', 'stopped'):
        # Consider an instance "running if not stopped / terminated
        # and "stopped" if not starting, running, hence the overlap
        if status == "running":
            statuses = ('provisioning staging running'
                        ' stopping suspending suspended')
        else:
            statuses = 'stopping stopped terminated'
        filters = " OR ".join(
            f"status: {status}"
            for status in statuses.split())
    # If status was specified in the filter, use it instead
    if filter_gcp:
        if "status" in filter_gcp or not filters:
            filters = filter_gcp
        else:
            filters += f" AND ({filter_gcp})"
    return filters


def filters_openstack(filter_openstack, status):
    """
    Filters for Openstack
    """
    filters = {}
    if status == 'running':
        filters = {'status': 'ACTIVE'}
    elif status == 'stopped':
        filters = {'status': 'STOPPED'}
    # If instance-state-name was specified in the filter, use it instead
    if filter_openstack:
        if 'status' in {_[0] for _ in filter_openstack}:
            filters = {}
        filters.update({_[0]: _[1] for _ in filter_openstack})
    # https://docs.openstack.org/openstack/latest/reference/vm-states.html
    return filters
