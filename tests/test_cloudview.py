# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import argparse
import pytest
from cloudview.cloudview import port_number


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
