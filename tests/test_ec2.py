# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name,protected-access

import os
import pytest
from cloudview.ec2 import get_creds, EC2
from cloudview.instance import Instance

for var in os.environ:
    if var.startswith("AWS_"):
        os.environ.pop(var)


def test_get_creds(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "access_key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret_key")

    creds = get_creds()

    assert "key" in creds
    assert creds["key"] == "access_key"

    assert "secret" in creds
    assert creds["secret"] == "secret_key"


def test_get_creds_missing_env_vars():
    creds = get_creds()

    assert "key" not in creds
    assert "secret" not in creds


@pytest.fixture
def mock_ec2_driver(mocker):
    mock_driver = mocker.Mock()
    mocker.patch("libcloud.compute.providers.get_driver", return_value=mock_driver)
    return mock_driver


@pytest.fixture
def mock_ec2_instance():
    return Instance(
        id="instance-id-123",
        name="test-instance",
        state=0,
        size="t2.micro",
        extra={
            "instance_type": "t2.micro",
            "launch_time": "2023-04-19T13:04:22.000Z",
            "availability": "us-east-1a",
        },
    )


@pytest.fixture
def valid_creds():
    return {"key": "your_access_key", "secret": "your_secret_key"}


@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    monkeypatch.setattr(EC2, "_singleton_instances", {})


def test_list_instances_in_region(
    mock_ec2_driver, mock_ec2_instance, mocker, valid_creds
):
    mocker.patch("cloudview.ec2.get_creds", return_value=valid_creds)
    mock_ec2_driver.list_nodes.return_value = [mock_ec2_instance]

    ec2 = EC2(**valid_creds)
    ec2._drivers = {"us-east-1": mock_ec2_driver}

    instances = ec2.list_instances_in_region("us-east-1")
    assert len(instances) == 1
    assert instances[0].id == "instance-id-123"
    assert instances[0].name == "test-instance"
    assert instances[0].size == "t2.micro"


def test_get_instance(mock_ec2_driver, mock_ec2_instance, mocker, valid_creds):
    mocker.patch("cloudview.ec2.get_creds", return_value=valid_creds)
    mock_ec2_driver.list_nodes.return_value = [mock_ec2_instance]

    ec2 = EC2(**valid_creds)
    ec2.regions = ["us-east-1"]
    ec2._drivers = {"us-east-1": mock_ec2_driver}

    instance = ec2._get_instance("instance-id-123", {"region": "us-east-1"})
    assert isinstance(instance, Instance)
    assert instance.extra["instance_type"] == "t2.micro"


def test_get_instances(mock_ec2_driver, mock_ec2_instance, mocker, valid_creds):
    mocker.patch("cloudview.ec2.get_creds", return_value=valid_creds)
    mock_ec2_driver.list_nodes.return_value = [mock_ec2_instance]

    ec2 = EC2(**valid_creds)
    ec2.regions = ["us-east-1"]
    ec2._drivers = {"us-east-1": mock_ec2_driver}

    instances = ec2._get_instances()
    assert len(instances) == 1
    assert instances[0].id == "instance-id-123"
    assert instances[0].name == "test-instance"
    assert instances[0].size == "t2.micro"
