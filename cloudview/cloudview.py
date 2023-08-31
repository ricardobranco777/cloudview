#!/usr/bin/env python3
"""
Show all instances created on cloud providers
"""

import argparse
import os
import logging
import sys
import html
from json import JSONEncoder
from io import StringIO
from operator import itemgetter
from threading import Thread
from urllib.parse import urlencode, quote, unquote
from typing import Generator

from wsgiref.simple_server import make_server
from pyramid.view import view_config
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.request import Request

import yaml
import libcloud
from libcloud.compute.types import Provider, LibcloudError

from .ec2 import EC2
from .azure import Azure
from .gce import GCE
from .openstack import Openstack
from .instance import CSP, STATES
from .output import Output
from .utils import fix_date, read_file
from . import __version__


USAGE = f"""Usage: {os.path.basename(sys.argv[0])} [OPTIONS]
Options:
    -h, --help                          show this help message and exit
    -c, --config FILE                   path to clouds.yaml
    -l, --log debug|info|warning|error|critical
                                        logging level
    -o, --output text|html|json         output type
    -P, --providers ec2|gce|azure_arm|openstack
                                        list only specified providers
    -p, --port PORT                     run a web server on port PORT
    -r, --reverse                       reverse sort
    -s, --sort name|time|state          sort type
    -S, --states error|migrating|normal|paused|pending|rebooting|reconfiguring|running|starting|stopped|stopping|suspended|terminated|unknown|updating
                                        filter by instance state
    -T, --time TIME_FORMAT              time format as used by strftime(3)
    -V, --version                       show version and exit
    -v, --verbose                       be verbose
"""

PROVIDERS = {
    str(Provider.EC2): EC2,
    str(Provider.GCE): GCE,
    str(Provider.AZURE_ARM): Azure,
    str(Provider.OPENSTACK): Openstack,
}


def get_clients(
    config_file: str,
    provider: str = "",
    cloud: str = "",
) -> Generator[CSP | None, None, None]:
    """
    Get clients for cloud providers
    """
    config = yaml.full_load(read_file(config_file)) if config_file else {}
    providers = (
        (provider,)
        if provider
        else config["providers"].keys()
        if config
        else PROVIDERS.keys()
    )
    for xprovider in providers:
        if xprovider not in PROVIDERS:
            logging.error("Unsupported provider %s", xprovider)
            continue
        if PROVIDERS[xprovider] is None:
            continue
        clouds = (
            (cloud,)
            if cloud
            else config["providers"][xprovider].keys()
            if config
            else ("",)
        )
        for xcloud in clouds:
            try:
                creds = config["providers"][xprovider][xcloud] if config else {}
                yield PROVIDERS[xprovider](cloud=xcloud, **creds)
            except KeyError:
                logging.error("Unsupported provider/cloud %s/%s", xprovider, xcloud)
            except LibcloudError:
                pass


def print_instances(client: CSP) -> None:
    """
    Print instances
    """
    instances = [
        instance
        for instance in client.get_instances()
        if str(instance.state) in args.states
    ]
    if args.sort:
        instances.sort(
            key=itemgetter(args.sort, "name"), reverse=args.reverse  # type:ignore
        )
    for instance in instances:
        instance.provider = "/".join([instance.provider, instance.cloud])
        if args.output == "html":
            params = urlencode(instance.params)
            resource = "/".join([instance.provider.lower(), f"{instance.id}?{params}"])
            instance.href = f"instance/{resource}"
        instance.time = fix_date(instance.time, args.time if args.verbose else None)
        Output().info(instance)


def print_info() -> Response | None:
    """
    Print information about instances
    """
    sys.stdout = StringIO() if args.port else sys.stdout
    threads = []
    for client in get_clients(config_file=args.config):
        threads.append(Thread(target=print_instances, args=(client,)))
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


def handle_requests(request: Request) -> Response | None:
    """
    Handle HTTP requests
    """
    logging.info(request)
    response = print_info()
    return Response(response)


def test(request: Request | None = None) -> Response | None:
    """
    Used for testing
    """
    if request:
        logging.info(request)
        response = "OK"
        return Response(response)
    return None


def not_found():
    """
    Not found!
    """
    response = Response("Not found!")
    response.status_int = 404
    return response


def valid_elem(elem: str) -> bool:
    """
    Validates URL path component
    """
    return (
        0 < len(elem) < 64
        and elem.isascii()
        and "/" not in elem
        and elem == unquote(quote(elem, safe=""))
    )


@view_config(route_name="instance")
def handle_instance(request: Request) -> Response:
    """
    Handle HTTP requests for instances
    """
    logging.info(request)
    provider = request.matchdict["provider"]
    cloud = request.matchdict["cloud"]
    identifier = request.matchdict["identifier"]
    if provider not in PROVIDERS or not valid_elem(cloud) or not valid_elem(identifier):
        return not_found()
    client = list(get_clients(config_file=args.config, provider=provider, cloud=cloud))[
        0
    ]
    if client is not None:
        info = client.get_instance(identifier, **request.params)
    if client is None or info is None:
        return not_found()
    response = html.escape(
        JSONEncoder(default=str, indent=4, sort_keys=True).encode(info)
    )
    header = """<!DOCTYPE html><html><head><meta charset="utf-8">
    <link rel="shortcut icon" href="/favicon.ico"></head><body>"""
    footer = "</body></html>"
    return Response(f"{header}<pre>{response}</pre>{footer}")


def web_server():
    """
    Setup the WSGI server
    """
    with Configurator() as config:
        config.add_route("handle_requests", "/")
        config.add_view(handle_requests, route_name="handle_requests")
        config.add_route("test", "/test")
        config.add_view(test, route_name="test")
        config.add_route("instance", "instance/{provider}/{cloud}/{identifier}")
        config.scan()
        app = config.make_wsgi_app()
        server = make_server("0.0.0.0", args.port, app)
        server.serve_forever()


def parse_args() -> argparse.Namespace:
    """
    Parse command line options
    """
    argparser = argparse.ArgumentParser(usage=USAGE, add_help=False)
    argparser.add_argument("-c", "--config", default="")
    argparser.add_argument("-h", "--help", action="store_true")
    argparser.add_argument(
        "-l",
        "--log",
        default="warning",
        choices="debug info warning error critical".split(),
    )
    argparser.add_argument(
        "-o", "--output", default="text", choices=["text", "html", "json"]
    )
    argparser.add_argument("-p", "--port", type=port_number)
    argparser.add_argument(
        "-P", "--providers", action="append", choices=list(PROVIDERS.keys())
    )
    argparser.add_argument("-r", "--reverse", action="store_true")
    argparser.add_argument("-s", "--sort", choices=["name", "state", "time"])
    argparser.add_argument("-S", "--states", action="append", choices=STATES)
    argparser.add_argument("-T", "--time", default="%a %b %d %H:%M:%S %Z %Y")
    argparser.add_argument("-v", "--verbose", action="count")
    argparser.add_argument("-V", "--version", action="store_true")
    return argparser.parse_args()


def port_number(port: str) -> int:
    """
    Check port argument
    """
    if port.isdigit() and 1 <= int(port) <= 65535:
        return int(port)
    raise argparse.ArgumentTypeError(f"{port} is an invalid port number")


def main():
    """
    Main function
    """
    if not args.config:
        for file in (os.path.expanduser("~/clouds.yaml"), "clouds.yaml"):
            if os.path.isfile(file):
                args.config = file
    elif not os.path.isfile(args.config):
        sys.exit(f"ERROR: No such file: {args.config}")

    if not args.providers:
        args.providers = PROVIDERS.keys()
    for provider in PROVIDERS:
        if provider not in args.providers:
            PROVIDERS[provider] = None

    if not args.states:
        args.states = STATES
    args.states = set(args.states)

    fmt = "%(asctime)s %(levelname)-8s %(message)s" if args.port else None
    logging.basicConfig(format=fmt, stream=sys.stderr, level=args.log.upper())

    keys = {
        "provider": "<15",
        "name": "<50",
        "size": ">20",
        "state": ">10",
        "time": "<30",
        "location": "<15",
    }
    if args.verbose:
        keys.update({"id": ""})

    if args.port:
        args.output = "html"
    Output(type=args.output.lower(), keys=keys, refresh_seconds=600)

    if args.port:
        web_server()
        sys.exit(1)

    print_info()


if __name__ == "__main__":
    args = parse_args()

    if args.help:
        print(USAGE)
        sys.exit(0)
    elif args.version:
        print(f"cloudview {__version__}")
        print(f"Python {sys.version}")
        print(f"Libcloud {libcloud.__version__}")
        sys.exit(0)

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
