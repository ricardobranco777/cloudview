# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,too-few-public-methods,redefined-outer-name

import argparse
import pytest
from cloudview.cloudview import port_number, valid_elem, get_clients, PROVIDERS


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


class MockEC2:
    def __init__(self, cloud, **_):
        self.cloud = cloud


class MockGCE:
    def __init__(self, cloud, **_):
        self.cloud = cloud


@pytest.fixture
def mock_config():
    return {
        "providers": {
            "ec2": {"ec2_cloud": {"key": "value"}},
            "gce": {"gce_cloud": {"key": "value"}},
        }
    }


def test_get_clients_without_config(mocker):
    mocker.patch("cloudview.cloudview.os.path.isfile", return_value=False)
    mocker.patch.dict(
        PROVIDERS,
        {
            "ec2": MockEC2,
            "gce": MockGCE,
        },
    )
    mocker.patch("cloudview.cloudview.Config", autospec=True)  # Mock the Config class

    clients = list(get_clients("/path/to/test_config.yaml"))

    assert len(clients) == 2
    assert all(isinstance(client, (MockEC2, MockGCE)) for client in clients)


def test_get_clients_with_config(mock_config, mocker):
    mocker.patch("cloudview.cloudview.os.path.isfile", return_value=True)
    mocker.patch(
        "cloudview.cloudview.Config",
        autospec=True,
        return_value=mocker.Mock(get_config=lambda: mock_config),
    )
    mocker.patch.dict(
        PROVIDERS,
        {
            "ec2": MockEC2,
            "gce": MockGCE,
        },
    )

    clients = list(get_clients("/path/to/test_config.yaml"))

    assert len(clients) == 2
    assert all(isinstance(client, (MockEC2, MockGCE)) for client in clients)


def test_get_clients_with_valid_provider_cloud(mock_config, mocker):
    mocker.patch("cloudview.cloudview.os.path.isfile", return_value=True)
    mocker.patch(
        "cloudview.cloudview.Config",
        autospec=True,
        return_value=mocker.Mock(get_config=lambda: mock_config),
    )
    mocker.patch.dict(
        PROVIDERS,
        {
            "ec2": MockEC2,
            "gce": MockGCE,
        },
    )

    clients = list(
        get_clients("/path/to/test_config.yaml", provider="ec2", cloud="ec2_cloud")
    )

    assert len(clients) == 1
    assert isinstance(clients[0], MockEC2)


def test_get_clients_with_valid_provider(mock_config, mocker):
    mocker.patch("cloudview.cloudview.os.path.isfile", return_value=True)
    mocker.patch(
        "cloudview.cloudview.Config",
        autospec=True,
        return_value=mocker.Mock(get_config=lambda: mock_config),
    )
    mocker.patch.dict(
        PROVIDERS,
        {
            "ec2": MockEC2,
        },
    )

    clients = list(get_clients("/path/to/test_config.yaml", provider="ec2"))

    assert len(clients) == 1
    assert isinstance(clients[0], MockEC2)


def test_get_clients_without_provider(mock_config, mocker):
    mocker.patch("cloudview.cloudview.os.path.isfile", return_value=True)
    mocker.patch(
        "cloudview.cloudview.Config",
        autospec=True,
        return_value=mocker.Mock(get_config=lambda: mock_config),
    )
    mocker.patch.dict(
        PROVIDERS,
        {
            "ec2": MockEC2,
            "gce": MockGCE,
        },
    )

    clients = list(get_clients("/path/to/test_config.yaml"))

    assert len(clients) == 2
    assert all(isinstance(client, (MockEC2, MockGCE)) for client in clients)


def test_get_clients_with_unsupported_provider(mock_config, mocker, caplog):
    mocker.patch("cloudview.cloudview.os.path.isfile", return_value=True)
    mocker.patch(
        "cloudview.cloudview.Config",
        autospec=True,
        return_value=mocker.Mock(get_config=lambda: mock_config),
    )
    mocker.patch.dict(
        PROVIDERS,
        {
            "ec2": MockEC2,
        },
    )

    clients = list(
        get_clients("/path/to/test_config.yaml", provider="unsupported_provider")
    )

    assert len(clients) == 0
    assert "Unsupported provider" in caplog.records[0].message
