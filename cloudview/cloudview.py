#!/usr/bin/python3
#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Show all instances created on cloud providers
"""

import os
import re
import logging
import sys

from argparse import ArgumentParser
from datetime import datetime
from io import StringIO
from itertools import groupby
from operator import itemgetter
from threading import Thread
from wsgiref.simple_server import make_server

import jmespath
from jmespath.exceptions import JMESPathError

import timeago

from cachetools import cached, TTLCache
from dateutil import parser
from pytz import utc
from pyramid.view import view_config
from pyramid.config import Configurator
from pyramid.response import Response

from cloudview.amazon import AWS
from cloudview.az import Azure
from cloudview.gcp import GCP
from cloudview.nova import Nova
from cloudview.exceptions import FatalError
from cloudview.output import Output
from cloudview import __version__


USAGE = "Usage: " + os.path.basename(sys.argv[0]) + """ [OPTIONS]
Options:
    -h, --help                          show this help message and exit
    -l, --log debug|info|warning|error|critical
    -o, --output text|html|json|JSON    output type
    -p, --port PORT                     run a web server on port PORT
    -r, --reverse                       reverse sort
    -s, --sort name|time|status         sort type
    -S, --status stopped|running|all    filter by instance status
    -T, --time TIME_FORMAT              time format as used by strftime(3)
    -V, --version                       show version and exit
    -v, --verbose                       be verbose
Filter options:
    --filter-aws NAME VALUE             may be specified multiple times
    --filter-azure FILTER               Filter for Azure
    --filter-gcp FILTER                 Filter for GCP
    --filter-nova NAME VALUE            may be specified multiple times
"""

args = None


def fix_date(date):
    """
    Converts datetime object or string to local time or the
    timezone specified by the TZ environment variable
    """
    if isinstance(date, str):
        # The parser returns datetime objects
        date = parser.parse(date)
    if isinstance(date, datetime):
        # GCP doesn't return UTC dates
        date = utc.normalize(date)
        if args.verbose:
            # From Python 3.3 we can omit tz in datetime.astimezone()
            return date.astimezone().strftime(args.time)
        return timeago.format(date, datetime.now(tz=utc))
    return ""


def print_amazon_instances():
    """
    Print information about AWS EC2 instances
    """
    filters = []
    # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html
    if args.status in ('running', 'stopped'):
        # Consider an instance "running" if not stopped or terminated
        # and "stopped" if not pending or running, hence the overlap
        if args.status == "running":
            statuses = 'pending running stopping shutting-down'.split()
        else:
            statuses = 'stopping stopped shutting-down terminated'.split()
        filters = [['instance-state-name', _] for _ in statuses]
    # If instance-state-name was specified in the filter, use it instead
    if args.filter_aws:
        if 'instance-state-name' in {_[0] for _ in args.filter_aws}:
            filters = args.filter_aws
        else:
            filters.extend(args.filter_aws)
    # Compile filter using 'Name' & 'Values'
    filters = [
        {'Name': name, 'Values': [v for _, v in values]}
        for name, values in groupby(
            sorted(filters, key=itemgetter(0)), itemgetter(0))
    ]
    aws = AWS()
    instances = aws.get_instances(filters=filters)
    keys = {
        'name': itemgetter('InstanceId'),
        'time': itemgetter('LaunchTime', 'InstanceId'),
        'status': lambda k: (aws.get_status(k), k['InstanceId'])
    }
    instances.sort(key=keys[args.sort], reverse=args.reverse)
    if args.output == "JSON":
        Output().all(instances)
        return
    for instance in instances:
        Output().info(
            provider="AWS",
            name=instance['InstanceId'],
            instance_id=instance['InstanceId'],
            type=instance['InstanceType'],
            status=aws.get_status(instance),
            created=fix_date(instance['LaunchTime']),
            location=instance['Placement']['AvailabilityZone'])


def print_azure_instances():
    """
    Print information about Azure Compute instances
    """
    filters = ""
    # https://docs.microsoft.com/en-us/azure/virtual-machines/windows/states-lifecycle
    if args.status in ('running', 'stopped'):
        # Consider an instance "running" if not stopped / deallocated
        # and "stopped" if not starting or running, hence the overlap
        if args.status == "running":
            statuses = 'starting running stopping'
        else:
            statuses = 'stopping stopped deallocating deallocated'
        filters = " || ".join(
            "instance_view.statuses[1].code == 'PowerState/%s'" % status
            for status in statuses.split())
    # If status was specified in the filter, use it instead
    if args.filter_azure:
        if "instance_view.statuses" in args.filter_azure or not filters:
            filters = args.filter_azure
        else:
            filters += " && (%s)" % args.filter_azure
    if filters:
        try:
            filters = jmespath.compile(filters)
        except JMESPathError as exc:
            FatalError("Azure", exc)
    azure = Azure()
    instances = azure.get_instances(filters=filters if filters else None)
    keys = {
        'name': itemgetter('name'),
        'time': lambda k: (azure.get_date(k), k['name']),
        'status': lambda k: (azure.get_status(k), k['name'])
    }
    try:
        instances.sort(key=keys[args.sort], reverse=args.reverse)
    except TypeError:
        # instance['_date'] may be None
        pass
    if args.output == "JSON":
        Output().all(instances)
        return
    for instance in instances:
        Output().info(
            provider="Azure",
            name=instance['name'],
            instance_id=instance['vm_id'],
            type=instance['hardware_profile']['vm_size'],
            status=azure.get_status(instance),
            created=fix_date(azure.get_date(instance)),
            location=instance['location'])


def print_google_instances():
    """
    Print information about Google Compute instances
    """
    filters = ""
    # https://cloud.google.com/compute/docs/instances/instance-life-cycle
    # NOTE: The above list is incomplete. The API returns more statuses
    if args.status in ('running', 'stopped'):
        # Consider an instance "running if not stopped / terminated
        # and "stopped" if not starting, running, hence the overlap
        if args.status == "running":
            statuses = ('provisioning staging running'
                        ' stopping suspending suspended')
        else:
            statuses = 'stopping stopped terminated'
        filters = " OR ".join(
            "status: %s" % status
            for status in statuses.split())
    # If status was specified in the filter, use it instead
    if args.filter_gcp:
        if "status" in args.filter_gcp or not filters:
            filters = args.filter_gcp
        else:
            filters += " AND (%s)" % args.filter_gcp
    gcp = GCP()
    instances = gcp.get_instances(filters=filters if filters else None)
    keys = {
        'name': itemgetter('name'),
        'time': itemgetter('creationTimestamp', 'name'),
        'status': itemgetter('status', 'name'),
    }
    instances.sort(key=keys[args.sort], reverse=args.reverse)
    if args.output == "JSON":
        Output().all(instances)
        return
    for instance in instances:
        Output().info(
            provider="GCP",
            name=instance['name'],
            instance_id=instance['id'],
            type=instance['machineType'].rsplit('/', 1)[-1],
            status=gcp.get_status(instance),
            created=fix_date(instance['creationTimestamp']),
            location=instance['zone'].rsplit('/', 1)[-1])


def print_nova_instances():
    """
    Print information about Openstack instances
    """
    filters = {}
    if args.status == 'running':
        filters = {'status': 'ACTIVE'}
    elif args.status == 'stopped':
        filters = {'status': 'STOPPED'}
    # If instance-state-name was specified in the filter, use it instead
    if args.filter_nova:
        if 'status' in {_[0] for _ in args.filter_nova}:
            filters = {}
        filters.update({_[0]: _[1] for _ in args.filter_nova})
    # https://docs.openstack.org/nova/latest/reference/vm-states.html
    nova = Nova()
    instances = nova.get_instances(filters=filters)
    keys = {
        'name': itemgetter('name'),
        'time': itemgetter('created', 'name'),
        'status': lambda k: (nova.get_status(k), k['name'])
    }
    instances.sort(key=keys[args.sort], reverse=args.reverse)
    if args.output == "JSON":
        Output().all(instances)
        return
    for instance in instances:
        Output().info(
            provider="Openstack",
            name=instance['name'],
            instance_id=instance['id'],
            type=nova.get_instance_type(instance['flavor']['id']),
            status=nova.get_status(instance),
            created=fix_date(instance['created']),
            location=instance['OS-EXT-AZ:availability_zone'])


@cached(cache={})
def check_aws():
    """
    Returns True if AWS credentials exist
    """
    return (bool(args.filter_aws) or
            'AWS_ACCESS_KEY_ID' in os.environ or
            os.path.exists(
                os.environ.get(
                    'AWS_SHARED_CREDENTIALS_FILE',
                    os.path.expanduser("~/.aws/credentials"))))


@cached(cache={})
def check_azure():
    """
    Returns True if Azure credentials exist
    """
    return (bool(args.filter_azure) or
            any(v.startswith("AZURE_") for v in os.environ))


@cached(cache={})
def check_gcp():
    """
    Returns True if GCP credentials exist
    """
    return (bool(args.filter_gcp) or
            'GOOGLE_APPLICATION_CREDENTIALS' in os.environ)


@cached(cache={})
def check_nova():
    """
    Returns True if OpenStack credentials exist
    """
    return (bool(args.filter_nova) or
            any(v.startswith("OS_") for v in os.environ))


@cached(cache=TTLCache(maxsize=2, ttl=120))
def print_info():
    """
    Print information about instances
    """
    if args.port:
        sys.stdout = StringIO()
    Output().header()
    threads = []
    if check_aws():
        threads.append(Thread(target=print_amazon_instances))
    if check_azure():
        threads.append(Thread(target=print_azure_instances))
    if check_gcp():
        threads.append(Thread(target=print_google_instances))
    if check_nova():
        threads.append(Thread(target=print_nova_instances))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    Output().footer()
    if args.port:
        response = sys.stdout.getvalue()
        sys.stdout.close()
        return response
    return None


def handle_requests(request):
    """
    Handle HTTP requests
    """
    logging.info(request)
    response = print_info()
    return Response(response)


def test(request=None):
    """
    Used for testing
    """
    if request:
        logging.info(request)
        response = "OK"
        return Response(response)
    return None


@view_config(route_name='instance')
def handle_instance(request):
    """
    Handle HTTP requests for instances
    """
    import html
    from json import JSONEncoder

    logging.info(request)
    provider = request.matchdict['provider']
    instance = request.matchdict['id']
    response = None
    if re.match("(i-)?[0-9a-f-]+$", instance):
        if provider == "aws":
            response = AWS().get_instance(instance)
        elif provider == "azure":
            response = Azure().get_instance(instance)
        elif provider == "gcp":
            response = GCP().get_instance(instance)
        elif provider == "openstack":
            response = Nova().get_instance(instance)
    if response is None:
        response = Response('Not found!')
        response.status_int = 404
        return response
    response = html.escape(
        JSONEncoder(default=str, indent=4, sort_keys=True).encode(response))
    header = '''<!DOCTYPE html><html><head><meta charset="utf-8">
    <link rel="shortcut icon" href="/favicon.ico"></head><body>'''
    footer = '</body></html>'
    return Response('%s<pre>%s</pre>%s' % (header, response, footer))


def web_server():
    """
    Setup the WSGI server
    """
    with Configurator() as config:
        config.add_route('handle_requests', '/')
        config.add_view(handle_requests, route_name='handle_requests')
        config.add_route('test', '/test')
        config.add_view(test, route_name='test')
        config.add_route('instance', 'instance/{provider}/{id}')
        config.scan()
        app = config.make_wsgi_app()
        server = make_server('0.0.0.0', args.port, app)
        server.serve_forever()


def setup_logging():
    """
    Setup logging
    """
    fmt = "%(asctime)s %(levelname)-8s %(message)s" if args.port else None
    logging.basicConfig(format=fmt, stream=sys.stderr, level=args.log.upper())


def parse_args():
    """
    Parse command line options
    """
    argparser = ArgumentParser(usage=USAGE, add_help=False)
    argparser.add_argument('-h', '--help', action='store_true')
    argparser.add_argument('-l', '--log', default='error',
                           choices='debug info warning error critical'.split())
    argparser.add_argument('-o', '--output', default='text',
                           choices=['text', 'html', 'json', 'JSON'])
    argparser.add_argument('-p', '--port', type=int)
    argparser.add_argument('-r', '--reverse', action='store_true')
    argparser.add_argument('-s', '--sort', default='name',
                           choices=['name', 'status', 'time'])
    argparser.add_argument('-S', '--status', default='running',
                           choices=['all', 'running', 'stopped'])
    argparser.add_argument('-T', '--time', default="%a %b %d %H:%M:%S %Z %Y")
    argparser.add_argument('-v', '--verbose', action='count')
    argparser.add_argument('-V', '--version', action='store_true')
    argparser.add_argument('--filter-aws', nargs=2, action='append')
    argparser.add_argument('--filter-azure', type=str)
    argparser.add_argument('--filter-gcp', type=str)
    argparser.add_argument('--filter-nova', nargs=2, action='append')
    return argparser.parse_args()


def main():
    """
    Main function
    """
    global args  # pylint: disable=global-statement
    args = parse_args()

    if args.help or args.version:
        print(USAGE if args.help else __version__)
        sys.exit(0)

    setup_logging()

    keys_ = "provider name type status created location"
    fmt_ = ('{d[provider]:10}\t{d[name]:32}\t{d[type]:>23}\t'
            '{d[status]:>16}\t{d[created]:30}\t{d[location]:10}')
    if args.verbose:
        keys_ += " instance_id"
        fmt_ += "\t{d[instance_id]}"

    if args.port:
        args.output = "html"
    _ = Output(type=args.output.lower(), keys=keys_, fmt=fmt_)

    if args.port:
        web_server()
        sys.exit(1)

    print_info()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
