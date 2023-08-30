# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name,unused-argument,protected-access

import pytest
from cloudview.config import check_leafs, Config


@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    monkeypatch.setattr(Config, "_singleton_instances", {})


@pytest.fixture
def dummy_config_data():
    return {
        "file_path": "/path/to/file.txt",
        "nested": {
            "sub_file": "/path/to/sub_file.txt",
            "other_value": "not_a_path",
        },
        "non_string_value": 123,
    }


def test_check_leafs_no_files(dummy_config_data):
    check_leafs(dummy_config_data)  # No exceptions should be raised


def test_check_leafs_with_files(dummy_config_data, mocker):
    mocker.patch("os.path.isfile", side_effect=[True, False])
    mocker.patch("os.stat")
    with pytest.raises(RuntimeError) as exc_info:
        check_leafs(dummy_config_data)

    assert "group/world readable" in str(exc_info.value)


def test_config_initialization(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data="config data"))
    mocker.patch("os.stat")
    mocker.patch("os.fstat", return_value=mocker.Mock(st_mode=0o600))

    config = Config("/path/to/test_config.yaml")
    assert config.path == "/path/to/test_config.yaml"


def test_config_get_config(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data="key: value"))
    mocker.patch("os.fstat", return_value=mocker.Mock(st_mode=0o600))

    config = Config("/path/to/test_config.yaml")
    result = config.get_config()

    assert result == {"key": "value"}


def test_config_get_config_with_file_permissions_issue(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data="key: value"))
    mocker.patch("os.stat")
    mocker.patch("os.fstat", return_value=mocker.Mock(st_mode=0o644))

    with pytest.raises(RuntimeError):
        _ = Config("/path/to/test_config.yaml")
