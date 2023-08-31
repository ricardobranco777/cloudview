# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name,unused-argument

import pytest
from cloudview.cloudview import get_clients, Provider


@pytest.fixture
def mock_read_file(mocker):
    return mocker.patch("cloudview.cloudview.read_file")


@pytest.fixture
def mock_yaml(mocker):
    return mocker.patch("cloudview.cloudview.yaml.full_load")


def test_get_clients_supported_provider(mock_read_file, mock_yaml, mocker):
    mocker.patch(
        "cloudview.cloudview.PROVIDERS",
        {
            str(Provider.EC2): mocker.MagicMock(),
            str(Provider.GCE): mocker.MagicMock(),
            str(Provider.AZURE_ARM): mocker.MagicMock(),
            str(Provider.OPENSTACK): mocker.MagicMock(),
        },
    )

    mock_yaml.return_value = {
        "providers": {"ec2": {"cloud1": {}}},
    }

    clients = list(get_clients("/path/to/config_file.yaml", provider="ec2"))

    assert len(clients) == 1


def test_get_clients_unsupported_provider(mock_read_file, mock_yaml, mocker, caplog):
    mocker.patch(
        "cloudview.cloudview.PROVIDERS",
        {
            str(Provider.EC2): mocker.MagicMock(),
        },
    )

    mock_yaml.return_value = {
        "providers": {"invalid_provider": {"cloud1": {}}},
    }

    clients = list(get_clients("/path/to/config_file.yaml"))

    assert len(clients) == 0
    assert "Unsupported provider" in caplog.text


def test_get_clients_no_config_file(mock_read_file, mock_yaml, mocker):
    mocker.patch(
        "cloudview.cloudview.PROVIDERS",
        {
            str(Provider.EC2): mocker.MagicMock(),
            str(Provider.GCE): mocker.MagicMock(),
            str(Provider.AZURE_ARM): mocker.MagicMock(),
            str(Provider.OPENSTACK): mocker.MagicMock(),
        },
    )

    mock_read_file.return_value = None
    mock_yaml.return_value = None

    clients = list(get_clients(""))

    assert len(clients) == 4


def test_get_clients_supported_provider_no_config(mock_read_file, mock_yaml, mocker):
    mocker.patch(
        "cloudview.cloudview.PROVIDERS",
        {
            str(Provider.EC2): mocker.MagicMock(),
        },
    )

    mock_read_file.return_value = None
    mock_yaml.return_value = None

    clients = list(get_clients("", provider="ec2"))

    assert len(clients) == 1


def test_get_clients_unsupported_provider_no_config(
    mock_read_file, mock_yaml, mocker, caplog
):
    mocker.patch(
        "cloudview.cloudview.PROVIDERS",
        {
            str(Provider.EC2): mocker.MagicMock(),
        },
    )

    mock_read_file.return_value = None
    mock_yaml.return_value = None

    clients = list(get_clients("", provider="invalid_provider"))

    assert len(clients) == 0
    assert "Unsupported provider" in caplog.text
