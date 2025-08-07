#!/usr/bin/env python3
"""
Show all instances created on cloud providers
"""

import argparse
import os
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from operator import itemgetter
from typing import Any

import yaml
from libcloud.compute.types import Provider, LibcloudError

from .ec2 import EC2
from .azure import Azure
from .gce import GCE
from .openstack import Openstack
from .instance import CSP, Instance, STATES
from .utils import dateit, read_file
from . import __version__


PROVIDERS: dict[str, Any] = {
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
        else config["providers"].keys() if config else PROVIDERS.keys()
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
            else config["providers"][xprovider].keys() if config else ("",)
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


def get_instances(client: CSP) -> list[Instance]:
    """
    Get instances
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
    return instances


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
        "-p",
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


def main() -> None:
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
    output_format = "  ".join(f"{{{key}:{align}}}" for key, align in keys.items())
    print(output_format.format_map({key: key.upper() for key in keys}))

    clients = get_clients(config_file=args.config)
    if len(clients) > 0:
        with ThreadPoolExecutor(max_workers=len(clients)) as executor:
            for instances in executor.map(get_instances, clients):
                for instance in instances:
                    instance.provider = f"{instance.provider}/{instance.cloud}"
                    assert not isinstance(instance.time, str)
                    instance.time = dateit(instance.time, args.time)
                    print(output_format.format_map(instance.__dict__))


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
