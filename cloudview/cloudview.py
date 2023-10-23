#!/usr/bin/env python3
"""
Show all instances created on cloud providers
"""

import argparse
import os
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from json import JSONEncoder
from io import StringIO
from operator import itemgetter
from urllib.parse import urlencode, quote, unquote

from wsgiref.simple_server import make_server
from pyramid.view import view_config
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.request import Request

import yaml
from libcloud.compute.types import Provider, LibcloudError

from .ec2 import EC2
from .azure import Azure
from .gce import GCE
from .openstack import Openstack
from .instance import CSP, STATES
from .output import Output
from .utils import dateit, read_file
from . import __version__


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
) -> list[CSP]:
    """
    Get clients for cloud providers
    """
    config = yaml.safe_load(read_file(config_file)) if config_file else {}
    providers = (
        (provider,)
        if provider
        else config["providers"].keys()
        if config
        else PROVIDERS.keys()
    )
    clients = []
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
                clients.append(PROVIDERS[xprovider](cloud=xcloud, **creds))
            except KeyError:
                logging.error("Unsupported provider/cloud %s/%s", xprovider, xcloud)
            except LibcloudError:
                pass
    return clients


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
        instance.time = dateit(instance.time, args.time)
        Output().info(instance)


def print_info() -> Response | None:
    """
    Print information about instances
    """
    clients = get_clients(config_file=args.config)
    sys.stdout = StringIO() if args.port else sys.stdout
    Output().header()
    if len(clients) > 0:
        with ThreadPoolExecutor(max_workers=len(clients)) as executor:
            executor.map(print_instances, clients)
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
    response = Response("Not found!", status=404)
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
    instance_id = request.matchdict["instance_id"]
    if (
        provider not in PROVIDERS
        or not valid_elem(cloud)
        or not valid_elem(instance_id)
    ):
        return not_found()
    client = list(get_clients(config_file=args.config, provider=provider, cloud=cloud))[
        0
    ]
    if client is not None:
        info = client.get_instance(instance_id, **request.params)
    if client is None or info is None:
        return not_found()
    response = JSONEncoder(default=str, indent=4, sort_keys=True).encode(info.extra)
    return Response(response, content_type='application/json; charset=utf-8')


def web_server():
    """
    Setup the WSGI server
    """
    with Configurator() as config:
        config.add_route("handle_requests", "/")
        config.add_view(handle_requests, route_name="handle_requests")
        config.add_route("test", "/test")
        config.add_view(test, route_name="test")
        config.add_route("instance", "instance/{provider}/{cloud}/{instance_id}")
        config.scan()
        app = config.make_wsgi_app()
        server = make_server("0.0.0.0", args.port, app)
        server.serve_forever()


def parse_args() -> argparse.Namespace:
    """
    Parse command line options
    """
    version = f"cloudview {__version__}"
    argparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="output fields for --fields: provider,name,id,size,state,time,location",
    )
    argparser.add_argument("-c", "--config", type=str, help="path to clouds.yaml")
    argparser.add_argument(
        "-f",
        "--fields",
        default="provider,name,size,state,time,location",
        help="output fields",
    )
    argparser.add_argument(
        "-l",
        "--log",
        default="error",
        choices=["none", "debug", "info", "warning", "error", "critical"],
        help="logging level",
    )
    argparser.add_argument(
        "-o",
        "--output",
        default="text",
        choices=["text", "html", "json"],
        help="output type",
    )
    argparser.add_argument(
        "-p", "--port", type=port_number, help="run a web server on specified port"
    )
    argparser.add_argument(
        "-P",
        "--providers",
        action="append",
        choices=list(PROVIDERS.keys()),
        help="list only specified providers",
    )
    argparser.add_argument("-r", "--reverse", action="store_true", help="reverse sort")
    argparser.add_argument(
        "-s", "--sort", choices=["name", "state", "time"], help="sort type"
    )
    argparser.add_argument(
        "-S",
        "--states",
        action="append",
        choices=STATES,
        help="filter by instance state",
    )
    argparser.add_argument(
        "-t",
        "--time",
        default="%a %b %d %H:%M:%S %Z %Y",
        metavar="TIME_FORMAT",
        help="strftime format or age|timeago",
    )
    argparser.add_argument("-v", "--verbose", action="count", help="be verbose")
    argparser.add_argument("--version", action="version", version=version)
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

    keys = {
        "provider": "<15",
        "name": "<50",
        "size": ">20",
        "state": ">10",
        "time": "<15" if args.time in {"age", "timeago"} else "<30",
        "location": "<15",
    }
    keys = {key: keys.get(key, "") for key in args.fields.split(",")}

    if args.verbose:
        keys |= {"id": ""}

    if args.port:
        args.output = "html"
    Output(type=args.output.lower(), keys=keys, refresh_seconds=600)

    if args.port:
        web_server()
        sys.exit(1)

    print_info()


if __name__ == "__main__":
    args = parse_args()
    if args.log == "none":
        logging.disable()
    else:
        logging.basicConfig(
            format="%(asctime)s %(levelname)-8s %(message)s",
            stream=sys.stderr,
            level=args.log.upper(),
        )
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
