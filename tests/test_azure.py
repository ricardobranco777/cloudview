# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name,protected-access

import os
import pytest
from libcloud.compute.types import LibcloudError
from cloudview.azure import get_creds, Azure
from cloudview.instance import Instance

for var in os.environ:
    if var.startswith(("AZURE_", "ARM_")):
        os.environ.pop(var)


def test_get_creds(monkeypatch):
    monkeypatch.setenv("AZURE_CLIENT_ID", "client_id")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "client_secret")
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant_id")
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "subscription_id")

    creds = get_creds()

    assert "key" in creds
    assert creds["key"] == "client_id"

    assert "secret" in creds
    assert creds["secret"] == "client_secret"

    assert "tenant_id" in creds
    assert creds["tenant_id"] == "tenant_id"

    assert "subscription_id" in creds
    assert creds["subscription_id"] == "subscription_id"


def test_get_creds_with_multiple_env_vars(monkeypatch):
    monkeypatch.setenv("ARM_CLIENT_ID", "client_id")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "client_secret")
    monkeypatch.setenv("ARM_TENANT_ID", "tenant_id")
    monkeypatch.setenv("ARM_SUBSCRIPTION_ID", "subscription_id")

    creds = get_creds()

    assert "key" in creds
    assert creds["key"] == "client_id"

    assert "secret" in creds
    assert creds["secret"] == "client_secret"

    assert "tenant_id" in creds
    assert creds["tenant_id"] == "tenant_id"

    assert "subscription_id" in creds
    assert creds["subscription_id"] == "subscription_id"


def test_get_creds_missing_env_vars():
    creds = get_creds()

    assert "key" not in creds
    assert "secret" not in creds
    assert "tenant_id" not in creds
    assert "subscription_id" not in creds


# Use the "monkeypatch" fixture to reset the singleton instance before each test
@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    monkeypatch.setattr(Azure, "_instances", {})


@pytest.fixture
def valid_creds():
    return {
        "tenant_id": "test_tenant",
        "subscription_id": "test_subscription",
        "key": "test_key",
        "secret": "test_secret",
    }


@pytest.fixture
def mock_get_driver(mocker):
    return mocker.patch("libcloud.compute.providers.get_driver")


@pytest.fixture
def mock_driver(mocker):
    return mocker.Mock()


@pytest.fixture
def mock_instance(mocker):
    return mocker.Mock(
        id="test_instance_id",
        name="test_instance",
        state="running",
        extra={
            "id": "test_instance_id",
            "name": "test_instance",
            "size": "Standard_B1ms",
            "state": "running",
            "properties": {
                "vmId": "test_instance_id",
                "hardwareProfile": {"vmSize": "Standard_B1ms"},
                "timeCreated": "2023-02-20T09:18:54.0380468+00:00",
            },
            "location": "test_location",
        },
    )


def test_azure_init_with_valid_creds(mocker, mock_get_driver, valid_creds):
    mock_get_driver.return_value = mocker.Mock()
    azure = Azure(cloud="test_cloud", **valid_creds)

    assert azure.cloud == "test_cloud"
    assert azure.creds == (
        "test_tenant",
        "test_subscription",
        "test_key",
        "test_secret",
    )
    assert azure.options == {
        "ex_resource_group": None,
        "ex_fetch_nic": False,
        "ex_fetch_power_state": False,
    }
    assert azure._driver is None


def test_azure_init_with_missing_creds(mocker, mock_get_driver):
    mock_get_driver.return_value = mocker.Mock()
    creds = {}
    with pytest.raises(LibcloudError):
        Azure(cloud="test_cloud", **creds)


def test_azure_get_instance_with_valid_identifier(
    mock_driver, mock_instance, valid_creds
):
    mock_driver.ex_get_node.return_value = mock_instance
    azure = Azure(cloud="test_cloud", **valid_creds)
    azure._driver = mock_driver

    result = azure._get_instance("test_identifier", params={"id": "test_instance_id"})

    assert isinstance(result, Instance)
    assert result.extra["id"] == "test_instance_id"
    assert result.extra["name"] == "test_instance"
    assert result.extra["size"] == "Standard_B1ms"
    assert result.extra["state"] == "running"
    assert result.extra["location"] == "test_location"


def test_azure_get_instance_with_invalid_identifier(mock_driver, valid_creds):
    mock_driver.ex_get_node.side_effect = LibcloudError("Node not found")
    azure = Azure(cloud="test_cloud", **valid_creds)
    azure._driver = mock_driver

    result = azure._get_instance("test_identifier", params={"id": "non_existent_id"})

    assert result is None


def test_azure_get_instances(mock_driver, mock_instance, valid_creds):
    mock_driver.list_nodes.return_value = [mock_instance]
    azure = Azure(cloud="test_cloud", **valid_creds)
    azure._driver = mock_driver

    result = azure._get_instances()

    assert len(result) == 1
    assert isinstance(result[0], Instance)
    assert result[0].id == "test_instance_id"
    assert result[0].size == "Standard_B1ms"
    assert result[0].state == "running"
    assert result[0].location == "test_location"


def test_azure_get_instances_with_driver_exception(mock_driver):
    mock_driver.list_nodes.side_effect = LibcloudError("Error listing nodes")
    with pytest.raises(LibcloudError):
        azure = Azure(cloud="test_cloud")
        azure._driver = mock_driver
        result = azure._get_instances()
        assert len(result) == 0
