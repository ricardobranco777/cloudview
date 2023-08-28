# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name,unused-argument,protected-access

import json
import pytest
from libcloud.compute.types import LibcloudError
from cloudview.gce import get_creds, GCE
from cloudview.instance import Instance


@pytest.fixture
def mock_open(mocker):
    return mocker.patch("builtins.open")


@pytest.fixture
def mock_isfile(mocker):
    return mocker.patch("os.path.isfile")


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "valid_creds.json")
    yield
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS")


def test_get_creds_with_valid_creds_file_and_env_var(mock_open, mock_isfile, mock_env):
    creds_data = {
        "project_id": "test_project",
        "client_email": "test_user@example.com",
    }
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
        creds_data
    )
    mock_isfile.return_value = True

    creds = get_creds({})

    assert "key" in creds
    assert creds["key"] == "valid_creds.json"
    assert "project" in creds
    assert creds["project"] == "test_project"
    assert "user_id" in creds
    assert creds["user_id"] == "test_user@example.com"


def test_get_creds_with_missing_attributes_in_creds_file_and_env_var(
    mock_open, mock_isfile, mock_env
):
    creds_data = {
        "project_id": "test_project",
    }
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
        creds_data
    )
    mock_isfile.return_value = True

    with pytest.raises(KeyError):
        creds = get_creds({})
        assert creds is None


def test_get_creds_without_creds_file_and_env_var(mock_isfile, mock_env):
    creds = get_creds({"project": "test_project", "user_id": "test_user@example.com"})

    assert "key" not in creds
    assert "project" in creds
    assert creds["project"] == "test_project"
    assert "user_id" in creds
    assert creds["user_id"] == "test_user@example.com"


def test_get_creds_with_invalid_creds_file_and_env_var(
    mock_open, mock_isfile, mock_env
):
    mock_open.return_value.__enter__.return_value.read.return_value = "invalid_json"
    mock_isfile.return_value = True

    with pytest.raises(json.decoder.JSONDecodeError):
        creds = get_creds({})
        assert creds is None


# Fixture to reset the singleton instance before each test
@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    monkeypatch.setattr(GCE, "_instances", {})


@pytest.fixture
def valid_creds():
    return {
        "project": "test_project",
        "user_id": "test_user",
        "key": "test_key",
    }


@pytest.fixture
def mock_get_driver(mocker):
    return mocker.patch("libcloud.compute.providers.get_driver")


@pytest.fixture
def mock_driver(mocker):
    return mocker.Mock()


@pytest.fixture
def mock_zone(mocker):
    return mocker.Mock(
        name="test_zone",
        status="UP",
        extra={"name": "test_zone", "status": "UP"},
    )


@pytest.fixture
def mock_instance(mocker):
    return mocker.Mock(
        name="test_instance",
        id="test_instance_id",
        state="running",
        extra={
            "name": "test_instance",
            "size": "test_size",
            "state": "running",
            "location": "test_zone",
            "machineType": "projects/test_project/machineTypes/test_size",
            "creationTimestamp": "2023-08-28T10:05:47.723-07:00",
            "zone": mocker.Mock(name="test_zone"),
        },
    )


def test_gce_init_with_valid_creds(mocker, mock_get_driver, valid_creds):
    mock_get_driver.return_value = mocker.Mock()
    gce = GCE(cloud="test_cloud", **valid_creds)

    assert gce.cloud == "test_cloud"
    assert gce.user_id == "test_user"
    assert gce.creds == {
        "project": "test_project",
        "key": "test_key",
    }
    assert gce._driver is None


def test_gce_init_with_missing_creds(mocker, mock_get_driver):
    mock_get_driver.return_value = mocker.Mock()
    creds = {}
    with pytest.raises(LibcloudError):
        GCE(cloud="test_cloud", **creds)


def test_gce_get_instance_with_valid_identifier(
    mocker, mock_driver, mock_instance, valid_creds
):
    mock_driver.ex_get_node.return_value = mock_instance
    gce = GCE(cloud="test_cloud", **valid_creds)
    gce._driver = mock_driver

    result = gce._get_instance("test_identifier", params={"name": "test_instance"})

    assert isinstance(result, Instance)
    assert result.extra["name"] == "test_instance"
    assert result.extra["size"] == "test_size"
    assert result.extra["state"] == "running"
    assert result.extra["location"] == "test_zone"


def test_gce_get_instance_with_invalid_identifier(mock_driver, valid_creds):
    mock_driver.ex_get_node.side_effect = LibcloudError("Node not found")
    gce = GCE(cloud="test_cloud", **valid_creds)
    gce._driver = mock_driver

    result = gce._get_instance(
        "test_identifier", params={"name": "non_existent_instance"}
    )

    assert result is None


def test_gce_get_instances_with_driver_exception(mock_driver):
    mock_driver.ex_list_zones.side_effect = LibcloudError("Error listing zones")
    with pytest.raises(LibcloudError):
        gce = GCE(cloud="test_cloud")
        gce._driver = mock_driver
        result = gce._get_instances()
        assert len(result) == 0


def test_gce_list_zones(mocker, mock_driver, valid_creds, mock_zone):
    mock_zone.name = "test_zone"  # Set the name attribute of the mock_zone
    mock_driver.ex_list_zones.return_value = [mock_zone]
    gce = GCE(cloud="test_cloud", **valid_creds)
    gce._driver = mock_driver

    result = gce.list_zones()
    assert len(result) == 1
    assert result[0].name == "test_zone"
    assert result[0].status == "UP"


def test_gce_list_instances_in_zone(
    mocker, mock_driver, valid_creds, mock_zone, mock_instance
):
    mock_instance.name = "test_instance"  # Set the name attribute of the mock_instance
    mock_driver.list_nodes.return_value = [mock_instance]
    gce = GCE(cloud="test_cloud", **valid_creds)
    gce._driver = mock_driver

    result = gce.list_instances_in_zone(mock_zone)
    assert len(result) == 1
    assert result[0].name == "test_instance"
    assert result[0].id == "test_instance_id"
    assert result[0].state == "running"


def test_gce_get_instances(mocker, mock_driver, mock_zone, mock_instance, valid_creds):
    mock_zone.name = "test_zone"  # Set the name attribute of the mock_zone
    mock_instance.name = "test_instance"  # Set the name attribute of the mock_instance
    mock_driver.ex_list_zones.return_value = [mock_zone]
    mock_driver.list_nodes.return_value = [mock_instance]
    mocker.patch.object(GCE, "list_instances_in_zone", return_value=[mock_instance])
    mocker.patch.object(GCE, "list_zones", return_value=[mock_zone])

    gce = GCE(cloud="test_cloud", **valid_creds)
    gce._driver = mock_driver

    result = gce._get_instances()

    assert len(result) == 1
    assert isinstance(result[0], Instance)
    assert result[0].id == "test_instance_id"
    assert result[0].size == "test_size"
    assert result[0].state == "running"
