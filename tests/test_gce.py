# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name,unused-argument

import json
import pytest
from cloudview.gce import get_creds


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
