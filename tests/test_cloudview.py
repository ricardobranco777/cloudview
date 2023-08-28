# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,too-few-public-methods

import argparse
import logging
from pathlib import Path
import pytest
from libcloud.compute.types import Provider, LibcloudError
from cloudview.cloudview import port_number, get_clients


class EC2:
    pass


def test_valid_port_number():
    valid_ports = ["1", "80", "443", "65535"]
    for port in valid_ports:
        result = port_number(port)
        assert result == int(port)


def test_invalid_port_number_below_range():
    invalid_ports = ["0", "-1", "-100", "65536", "99999"]
    for port in invalid_ports:
        with pytest.raises(argparse.ArgumentTypeError):
            port_number(port)


def test_invalid_port_number_non_numeric():
    invalid_ports = ["abc", "1a2b", "port"]
    for port in invalid_ports:
        with pytest.raises(argparse.ArgumentTypeError):
            port_number(port)


def test_get_clients_unsupported_provider(caplog):
    config_file = Path("config_file_path2")

    with caplog.at_level(logging.ERROR):
        clients = list(get_clients(config_file=config_file, provider="UNSUPPORTED"))

    assert len(clients) == 0
    assert "Unsupported provider" in caplog.text


def test_get_clients_libcloud_error(mocker, caplog):
    config_file = Path("config_file_path4")

    EC2.__init__ = mocker.MagicMock(side_effect=LibcloudError("Test LibcloudError"))

    with caplog.at_level(logging.ERROR):
        clients = list(get_clients(config_file=config_file, provider=str(Provider.EC2)))

    assert len(clients) == 0
    assert "Unsupported provider" not in caplog.text  # LibcloudError is caught silently
