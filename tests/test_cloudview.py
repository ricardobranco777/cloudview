# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,too-few-public-methods,redefined-outer-name

import argparse
import pytest
from cloudview.cloudview import port_number, valid_elem


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


def test_valid_elem_valid_input():
    assert valid_elem("example") is True
    assert valid_elem("path123") is True


def test_valid_elem_empty_input():
    assert valid_elem("") is False


def test_valid_elem_too_long_input():
    assert valid_elem("a" * 64) is False


def test_valid_elem_contains_slash():
    assert valid_elem("with/slash") is False


def test_valid_elem_non_ascii_input():
    assert valid_elem("résumé") is False


def test_valid_elem_url_encoding():
    assert valid_elem("hello%20world") is True


def test_valid_elem_url_decoding():
    assert valid_elem("hello world") is True
