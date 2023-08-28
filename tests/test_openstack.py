# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name,unused-argument,protected-access

import pytest
from libcloud.compute.types import LibcloudError
from cloudview.openstack import get_creds, Openstack
from cloudview.instance import Instance


@pytest.fixture
def mock_openstack_env(monkeypatch):
    env_vars = {
        "OS_AUTH_URL": "http://example.com",
        "OS_USERNAME": "test_user",
        "OS_PASSWORD": "test_password",
        "OS_USER_DOMAIN_NAME": "test_domain",
        "OS_PROJECT_NAME": "test_project",
    }
    for var, value in env_vars.items():
        monkeypatch.setenv(var, value)
    yield
    for var in env_vars:
        try:
            monkeypatch.delenv(var)
        except KeyError:
            pass


def test_get_creds_with_valid_auth_url(mock_openstack_env):
    creds = get_creds()

    assert "key" in creds
    assert creds["key"] == "test_user"
    assert "secret" in creds
    assert creds["secret"] == "test_password"
    assert "ex_domain_name" in creds
    assert creds["ex_domain_name"] == "test_domain"
    assert "ex_tenant_name" in creds
    assert creds["ex_tenant_name"] == "test_project"
    assert "ex_force_auth_url" in creds
    assert creds["ex_force_auth_url"] == "http://example.com"
    assert "ex_force_base_url" in creds
    assert creds["ex_force_base_url"] == "http://example.com:8774/v2.1"
    assert "api_version" in creds
    assert creds["api_version"] == "2.2"


def test_get_creds_with_missing_auth_url(mock_openstack_env, monkeypatch):
    monkeypatch.delenv("OS_AUTH_URL")
    creds = get_creds()

    assert not creds


# Fixture to reset the singleton instance before each test
@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    monkeypatch.setattr(Openstack, "_instances", {})


@pytest.fixture
def valid_creds():
    return {
        "tenant_name": "test_project",
        "user_domain_name": "test_domain",
        "key": "test_key",
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
        size="small",
        state="running",
        extra={
            "id": "test_instance_id",
            "name": "test_instance",
            "location": "test_location",
            "size": "small",
            "state": "running",
            "created": "2023-08-27T12:34:56Z",
            "availability_zone": "test_location",
            "flavorId": "test_size_id",
        },
    )


def test_openstack_init_with_valid_creds(mocker, mock_get_driver, valid_creds):
    mock_get_driver.return_value = mocker.Mock()
    openstack = Openstack(cloud="test_cloud", **valid_creds)

    assert openstack.cloud == "test_cloud"
    assert openstack.key == "test_key"
    assert openstack.creds == {
        "tenant_name": "test_project",
        "user_domain_name": "test_domain",
    }
    assert openstack.options == {"ex_all_tenants": False}
    assert openstack._driver is None


def test_openstack_init_with_missing_creds(mocker, mock_get_driver):
    mock_get_driver.return_value = mocker.Mock()
    creds = {}
    with pytest.raises(LibcloudError):
        Openstack(cloud="test_cloud", **creds)


def test_openstack_get_size(mocker, mock_driver, valid_creds):
    mock_size_1 = mocker.Mock(id="size_id_1")
    mock_size_1.name = "size_name_1"
    mock_size_2 = mocker.Mock(id="size_id_2")
    mock_size_2.name = "size_name_2"
    mock_driver.list_sizes.return_value = [mock_size_1, mock_size_2]
    openstack = Openstack(cloud="test_cloud", **valid_creds)
    openstack._driver = mock_driver

    result = openstack.get_size("size_id_1")
    assert result == "size_name_1"

    result = openstack.get_size("size_id_2")
    assert result == "size_name_2"

    result = openstack.get_size("unknown_size_id")
    assert result == "unknown"


def test_openstack_get_sizes(mocker, mock_driver, valid_creds):
    mock_driver.list_sizes.return_value = [
        mocker.Mock(id="size_id_1", name="size_name_1"),
        mocker.Mock(id="size_id_2", name="size_name_2"),
    ]
    openstack = Openstack(cloud="test_cloud", **valid_creds)
    openstack._driver = mock_driver

    result = openstack.get_sizes()
    assert len(result) == 2
    assert result[0].id == "size_id_1"
    assert result[1].id == "size_id_2"


def test_openstack_get_instance_with_valid_identifier(
    mocker, mock_driver, mock_instance, valid_creds
):
    mock_driver.ex_get_node_details.return_value = mock_instance
    openstack = Openstack(cloud="test_cloud", **valid_creds)
    openstack._driver = mock_driver

    result = openstack._get_instance("test_instance_id", {})

    assert isinstance(result, Instance)
    assert result.extra["id"] == "test_instance_id"
    assert result.extra["name"] == "test_instance"
    assert result.extra["size"] == "small"
    assert result.extra["state"] == "running"
    assert result.extra["location"] == "test_location"


def test_openstack_get_instance_with_invalid_identifier(mock_driver, valid_creds):
    mock_driver.ex_get_node_details.side_effect = LibcloudError("Node not found")
    openstack = Openstack(cloud="test_cloud", **valid_creds)
    openstack._driver = mock_driver

    result = openstack._get_instance("non_existent_id", {})

    assert result is None


def test_openstack_get_instances(mocker, mock_driver, mock_instance, valid_creds):
    mock_driver.list_nodes.return_value = [mock_instance]
    mocker.patch.object(Openstack, "get_size", return_value="small")

    openstack = Openstack(cloud="test_cloud", **valid_creds)
    openstack._driver = mock_driver

    result = openstack._get_instances()

    assert len(result) == 1
    assert isinstance(result[0], Instance)
    assert result[0].id == "test_instance_id"
    assert result[0].size == "small"
    assert result[0].state == "running"
    assert result[0].location == "test_location"


def test_openstack_get_instances_with_driver_exception(mock_driver):
    mock_driver.list_nodes.side_effect = LibcloudError("Error listing nodes")
    with pytest.raises(LibcloudError):
        openstack = Openstack(cloud="test_cloud")
        openstack._driver = mock_driver
        result = openstack._get_instances()
        assert len(result) == 0
