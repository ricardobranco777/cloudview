#!/usr/bin/env python3
"""
Show all instances created on cloud providers
"""

import argparse
import os
import re
import logging
import stat
import sys
import html
from json import JSONEncoder
from io import StringIO
from pathlib import Path
from operator import itemgetter
from threading import Thread
from typing import Dict, Optional

from wsgiref.simple_server import make_server
from pyramid.view import view_config
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.request import Request

from libcloud.compute.types import Provider, LibcloudError
import yaml

from .ec2 import EC2
from .azure import Azure
from .gce import GCE
from .openstack import Openstack
from .utils import fix_date
from .output import Output
from .instance import STATES
from . import __version__


USAGE = f"""Usage: {os.path.basename(sys.argv[0])} [OPTIONS]
Options:
    -h, --help                          show this help message and exit
    -c, --config FILE                   path to clouds.yaml
    -l, --log debug|info|warning|error|critical
                                        logging level
    -o, --output text|html|json         output type
    -p, --port PORT                     run a web server on port PORT
    -r, --reverse                       reverse sort
    -s, --sort none|name|time|state     sort type
    -S, --states error|migrating|normal|paused|pending|rebooting|reconfiguring|running|starting|stopped|stopping|suspended|terminated|unknown|updating
                                        filter by instance state
    -T, --time TIME_FORMAT              time format as used by strftime(3)
    -V, --version                       show version and exit
    -v, --verbose                       be verbose
"""

PROVIDERS = {
    str(Provider.EC2): EC2,
    str(Provider.AZURE_ARM): Azure,
    str(Provider.GCE): GCE,
    str(Provider.OPENSTACK): Openstack,
    "azure": Azure,
}


def print_instances(provider: str, cloud: str = "default", creds: Optional[Dict[str, str]] = None) -> None:
    """
    Print instances
    """
    if creds is None:
        creds = {}
    try:
        client = PROVIDERS[provider](cloud=cloud, **creds)
        instances = [
            instance for instance in client.get_instances()
            if str(instance.state) in args.states
        ]
    except LibcloudError:
        return
    if args.sort != "none":
        instances.sort(key=itemgetter(args.sort, 'name'), reverse=args.reverse)  # type:ignore
    for instance in instances:
        instance.time = fix_date(instance.time, args.time if args.verbose else None)
        Output().info(instance, **instance.__dict__)


def print_info() -> Optional[Response]:
    """
    Print information about instances
    """
    sys.stdout = StringIO() if args.port else sys.stdout
    threads = []
    if args.config.is_file():
        if not args.insecure and args.config.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            sys.exit(f"ERROR: {args.config} is group and world readable")
        with open(args.config, encoding="utf-8") as file:
            config = yaml.full_load(file)
        for cloud in config['providers']['gce']:
            keyfile = Path(config['providers']['gce'][cloud]['key'])
            if keyfile.is_file() and keyfile.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
                sys.exit(f"ERROR: {keyfile} is group and world readable")
        for provider in config['providers']:
            if provider not in PROVIDERS:
                logging.error("Unsupported provider %s", provider)
                continue
            for cloud in config['providers'][provider]:
                threads.append(Thread(target=print_instances, args=(provider, cloud, config['providers'][provider][cloud])))
    else:
        for provider in PROVIDERS:
            threads.append(Thread(target=print_instances, args=(provider,)))
    Output().header()
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


def handle_requests(request: Request) -> Optional[Response]:
    """
    Handle HTTP requests
    """
    logging.info(request)
    response = print_info()
    return Response(response)


def test(request: Optional[Request] = None) -> Optional[Response]:
    """
    Used for testing
    """
    if request:
        logging.info(request)
        response = "OK"
        return Response(response)
    return None


@view_config(route_name='instance')
def handle_instance(request: Request) -> Response:
    """
    Handle HTTP requests for instances
    """
    logging.info(request)
    provider = request.matchdict['provider']
    cloud = request.matchdict['cloud']
    instance = request.matchdict['id']
    info = None
    if re.match("(i-)?[0-9a-f-]+$", instance):
        cls = PROVIDERS.get(provider)
        if cls is not None:
            info = cls(cloud=cloud).get_instance(instance)
    if info is None:
        response = Response('Not found!')
        response.status_int = 404
        return response
    response = html.escape(JSONEncoder(default=str, indent=4, sort_keys=True).encode(info))
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
        config.add_route('instance', 'instance/{provider}/{cloud}/{id}')
        config.scan()
        app = config.make_wsgi_app()
        server = make_server('0.0.0.0', args.port, app)
        server.serve_forever()


def parse_args() -> argparse.Namespace:
    """
    Parse command line options
    """
    argparser = argparse.ArgumentParser(usage=USAGE, add_help=False)
    argparser.add_argument('-c', '--config', default=os.path.expanduser("~/clouds.yaml"), type=Path)
    argparser.add_argument('-h', '--help', action='store_true')
    argparser.add_argument('--insecure', action='store_true')
    argparser.add_argument('-l', '--log', default='error',
                           choices='debug info warning error critical'.split())
    argparser.add_argument('-o', '--output', default='text',
                           choices=['text', 'html', 'json', 'JSON'])
    argparser.add_argument('-p', '--port', type=port_number)
    argparser.add_argument('-r', '--reverse', action='store_true')
    argparser.add_argument('-s', '--sort', default='none',
                           choices=['none', 'name', 'state', 'time'])
    argparser.add_argument('-S', '--states', action='append',
                           choices=STATES)
    argparser.add_argument('-T', '--time', default="%a %b %d %H:%M:%S %Z %Y")
    argparser.add_argument('-v', '--verbose', action='count')
    argparser.add_argument('-V', '--version', action='store_true')
    return argparser.parse_args()


def port_number(port: str) -> int:
    """
    Check port argument
    """
    if port.isdigit() and 1 <= int(port) <= 65535:
        return int(port)
    raise argparse.ArgumentTypeError(f"{port} is an invalid port number")


args = parse_args()


def main():
    """
    Main function
    """
    if args.help or args.version:
        print(USAGE if args.help else __version__)
        sys.exit(0)

    if not args.states:
        args.states = STATES
    args.states = set(args.states)

    fmt = "%(asctime)s %(levelname)-8s %(message)s" if args.port else None
    logging.basicConfig(format=fmt, stream=sys.stderr, level=args.log.upper())

    keys = "provider name size state time location".split()
    fmt = '{d[provider]:10}  {d[name]:50}  {d[size]:>20}  {d[state]:>14}  {d[time]:30}  {d[location]:15}'
    if args.verbose:
        keys.append("id")
        fmt += "  {d[id]}"

    if args.port:
        args.output = "html"
    _ = Output(output_format=args.output.lower(), keys=keys, fmt=fmt)

    if args.port:
        web_server()
        sys.exit(1)

    print_info()
