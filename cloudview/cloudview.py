#!/usr/bin/env python3
#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Show all instances created on cloud providers
"""

import argparse
import os
import re
import logging
import sys

import html
from json import JSONEncoder

from io import StringIO
from operator import itemgetter
from threading import Thread
from wsgiref.simple_server import make_server

from cachetools import cached, TTLCache
from pyramid.view import view_config
from pyramid.config import Configurator
from pyramid.response import Response

import openstack
from .aws import AWS
from .az import Azure
from .gcp import GCP
from .openstack import Openstack
from .utils import fix_date
from .output import Output
from .filters import filters_aws, filters_azure, filters_gcp, filters_openstack
from . import __version__


USAGE = f"""Usage: {os.path.basename(sys.argv[0])} [OPTIONS]
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
    --insecure                          do not validate TLS certificates
Filter options:
    --filter-aws NAME VALUE             may be specified multiple times
    --filter-azure FILTER               Filter for Azure
    --filter-gcp FILTER                 Filter for GCP
    --filter-openstack NAME VALUE       may be specified multiple times
"""

args = None  # pylint: disable=invalid-name


def print_amazon_instances():
    """
    Print information about AWS EC2 instances
    """
    filters = filters_aws(args.filter_aws, args.status)
    aws = AWS()
    instances = aws.get_instances(filters=filters)
    keys = {
        'name': lambda k: aws.get_tags(k).get('Name', k['InstanceId']),
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
            name=aws.get_tags(instance).get('Name', instance['InstanceId']),
            instance_id=instance['InstanceId'],
            size=instance['InstanceType'],
            status=aws.get_status(instance),
            created=fix_date(instance['LaunchTime'], args.time if args.verbose else None),
            location=instance['Placement']['AvailabilityZone'])


def print_azure_instances():
    """
    Print information about Azure Compute instances
    """
    filters = filters_azure(args.filter_azure, args.status)
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
            size=instance['hardware_profile']['vm_size'],
            status=azure.get_status(instance),
            created=fix_date(azure.get_date(instance), args.time if args.verbose else None),
            location=instance['location'])


def print_google_instances():
    """
    Print information about Google Compute instances
    """
    filters = filters_gcp(args.filter_gcp, args.status)
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
            size=instance['machineType'].rsplit('/', 1)[-1],
            status=gcp.get_status(instance),
            created=fix_date(instance['creationTimestamp'], args.time if args.verbose else None),
            location=instance['zone'].rsplit('/', 1)[-1])


def print_openstack_instances(cloud=None):
    """
    Print information about Openstack instances
    """
    filters = filters_openstack(args.filter_openstack, args.status)
    ostack = Openstack(cloud=cloud, insecure=args.insecure)
    instances = ostack.get_instances(filters=filters)
    keys = {
        'name': itemgetter('name'),
        'time': itemgetter('created', 'name'),
        'status': lambda k: (ostack.get_status(k), k['name'])
    }
    instances.sort(key=keys[args.sort], reverse=args.reverse)
    if args.output == "JSON":
        Output().all(instances)
        return
    for instance in instances:
        Output().info(
            provider=cloud or "Openstack",
            name=instance['name'],
            instance_id=instance['id'],
            size=ostack.get_instance_type(instance['flavor']['id']) if 'id' in instance['flavor'] else instance['flavor']['original_name'],
            status=ostack.get_status(instance),
            created=fix_date(instance['created'], args.time if args.verbose else None),
            location=instance['OS-EXT-AZ:availability_zone'])


@cached(cache=TTLCache(maxsize=2, ttl=120))
def print_info():
    """
    Print information about instances
    """
    if args.port:
        sys.stdout = StringIO()
    Output().header()
    threads = []
    if check_aws:
        threads.append(Thread(target=print_amazon_instances))
    if check_azure:
        threads.append(Thread(target=print_azure_instances))
    if check_gcp:
        threads.append(Thread(target=print_google_instances))
    if check_openstack:
        clouds = openstack.config.OpenStackConfig(
            load_envvars=False).get_cloud_names()
        if set(clouds) == set(['defaults']):
            clouds = [None]
        for cloud in clouds:
            threads.append(
                Thread(target=print_openstack_instances, args=(cloud,)))
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
        else:
            response = Openstack(cloud=provider, insecure=args.insecure).get_instance(instance)
    if response is None:
        response = Response('Not found!')
        response.status_int = 404
        return response
    response = html.escape(
        JSONEncoder(default=str, indent=4, sort_keys=True).encode(response))
    header = '''<!DOCTYPE html><html><head><meta charset="utf-8">
    <link rel="shortcut icon" href="/favicon.ico"></head><body>'''
    footer = '</body></html>'
    return Response(f'{header}<pre>{response}</pre>{footer}')


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
    argparser = argparse.ArgumentParser(usage=USAGE, add_help=False)
    argparser.add_argument('-h', '--help', action='store_true')
    argparser.add_argument('-l', '--log', default='error',
                           choices='debug info warning error critical'.split())
    argparser.add_argument('-o', '--output', default='text',
                           choices=['text', 'html', 'json', 'JSON'])
    argparser.add_argument('-p', '--port', type=port_number)
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
    argparser.add_argument('--filter-openstack', nargs=2, action='append')
    return argparser.parse_args()


def port_number(port):
    """
    Check port argument
    """
    if port.isdigit() and 1 <= int(port) <= 65535:
        return int(port)
    raise argparse.ArgumentTypeError(f"{port} is an invalid port number")


args = parse_args()
check_aws = any([bool(args.filter_aws),
                'AWS_ACCESS_KEY_ID' in os.environ,
                 os.path.exists(os.getenv('AWS_SHARED_CREDENTIALS_FILE', os.path.expanduser("~/.aws/credentials")))])
check_azure = bool(args.filter_azure) or any(v.startswith("AZURE_") for v in os.environ)
check_gcp = bool(args.filter_gcp) or 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ
check_openstack = any([bool(args.filter_openstack),
                      any(v.startswith("OS_") for v in os.environ),
                      os.path.exists(os.path.expanduser("~/.config/openstack/clouds.yaml")),
                      os.path.exists("/etc/openstack/clouds.yaml")])


def main():
    """
    Main function
    """
    if args.help or args.version:
        print(USAGE if args.help else __version__)
        sys.exit(0)

    setup_logging()

    keys = "provider name size status created location"
    fmt = ('{d[provider]:10}\t{d[name]:32}\t{d[size]:>23}\t'
           '{d[status]:>16}\t{d[created]:30}\t{d[location]:10}')
    if args.verbose:
        keys += " instance_id"
        fmt += "\t{d[instance_id]}"

    if args.port:
        args.output = "html"
    _ = Output(output_format=args.output.lower(), keys=keys, fmt=fmt)

    if args.port:
        web_server()
        sys.exit(1)

    print_info()
