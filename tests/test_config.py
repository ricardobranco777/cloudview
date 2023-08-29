# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name,unused-argument,protected-access

import stat
from pathlib import Path
import pytest

from cloudview.config import check_permissions, check_leafs, Config


@pytest.fixture
def mock_stat(mocker):
    mock_result = mocker.Mock(
        st_mode=0o10777,
        st_mtime=float(0),
    )
    mocker.patch("os.stat", return_value=mock_result)
    return mock_result


def test_check_permissions_world_readable_not_insecure(mock_stat, caplog):
    mock_stat.st_mode = stat.S_IRWXG | stat.S_IRWXO

    path = Path("/path/file")
    with pytest.raises(SystemExit):
        check_permissions(path, insecure=False)

    assert "is world readable" in caplog.text
    assert "ERROR" in caplog.text


def test_check_permissions_world_readable_insecure(mock_stat, caplog):
    mock_stat.st_mode = stat.S_IRWXG | stat.S_IRWXO

    path = Path("/path/file")
    check_permissions(path, insecure=True)

    assert "is world readable" in caplog.text
    assert "WARNING" in caplog.text


def test_check_permissions_not_world_readable(mock_stat, caplog):
    mock_stat.st_mode = 0o600

    path = Path("/path/file")
    check_permissions(path, insecure=True)

    assert "is world readable" not in caplog.text
    assert "ERROR" not in caplog.text
    assert "WARNING" not in caplog.text


@pytest.fixture
def mock_isfile(mocker):
    return mocker.patch("os.path.isfile")


@pytest.fixture
def mock_check_permissions(mocker):
    return mocker.patch("cloudview.config.check_permissions")


def test_check_leafs_empty_dict(mock_isfile, mock_check_permissions):
    tree = {}
    check_leafs(tree)

    mock_isfile.assert_not_called()
    mock_check_permissions.assert_not_called()


def test_check_leafs_nested_dict_with_files(
    mocker, mock_isfile, mock_check_permissions
):
    mock_isfile.side_effect = [True, True, False]
    mock_check_permissions.return_value = None

    tree = {
        "key1": {
            "file": "/path/to/file.txt",
            "key2": {"subfile": "/path/to/subfile.txt"},
        },
        "key3": "not_a_file",
    }
    check_leafs(tree)

    mock_isfile.assert_has_calls(
        [
            mocker.call("/path/to/file.txt"),
            mocker.call("/path/to/subfile.txt"),
        ]
    )
    assert mock_check_permissions.call_count == 2


def test_check_leafs_nested_dict_with_relative_paths(
    mock_isfile, mock_check_permissions
):
    mock_isfile.return_value = False
    mock_check_permissions.return_value = None

    tree = {"key1": {"file": "relative/file.txt"}}
    check_leafs(tree)

    mock_isfile.assert_not_called()
    mock_check_permissions.assert_not_called()


def test_check_leafs_nested_dict_with_insecure_flag(
    mocker, mock_isfile, mock_check_permissions
):
    mock_isfile.side_effect = [True, True]
    mock_check_permissions.return_value = None

    tree = {
        "key1": {
            "file": "/path/to/file.txt",
            "key2": {"subfile": "/path/to/subfile.txt"},
        },
        "key3": "not_a_file",
    }
    check_leafs(tree, insecure=True)

    mock_isfile.assert_has_calls(
        [mocker.call("/path/to/file.txt"), mocker.call("/path/to/subfile.txt")]
    )
    assert mock_check_permissions.call_count == 2


@pytest.fixture
def mock_check_leafs(mocker):
    return mocker.patch("cloudview.config.check_leafs")


@pytest.fixture
def mock_open(mocker):
    return mocker.patch("builtins.open", mocker.mock_open(read_data="content"))


@pytest.fixture
def mock_yaml_load(mocker):
    return mocker.patch("yaml.full_load")


def test_get_config_cached(
    mock_stat, mock_check_permissions, mock_check_leafs, mock_yaml_load
):
    mock_stat.return_value.st_mtime = 12345.0
    config_instance = Config(Path("/path/to/config.yaml"))

    config_instance._config = {"key": "value"}

    config = config_instance.get_config()
    assert config == {"key": "value"}

    mock_check_permissions.assert_called_once_with(Path("/path/to/config.yaml"), False)
    mock_check_leafs.assert_not_called()
    mock_yaml_load.assert_not_called()


def test_get_config_not_cached(
    mock_stat, mock_check_permissions, mock_check_leafs, mock_open, mock_yaml_load
):
    mock_stat.return_value.st_mtime = 12345.0
    config_instance = Config(Path("/path/to/config2.yaml"))

    mock_yaml_load.return_value = {"new": "config"}

    config = config_instance.get_config()
    assert config == {"new": "config"}

    mock_check_permissions.assert_called_once_with(Path("/path/to/config2.yaml"), False)
    mock_check_leafs.assert_called_once()
    mock_yaml_load.assert_called_once()


def test_get_config_file_not_modified(
    mock_stat, mock_check_permissions, mock_check_leafs, mock_yaml_load
):
    mock_stat.return_value.st_mtime = 12345.0
    config_instance = Config(Path("/path/to/config3.yaml"))
    config_instance._config = {"cached": "config"}
    config_instance._last_modified_time = 12345.0

    config = config_instance.get_config()
    assert config == {"cached": "config"}

    mock_check_permissions.assert_called_once_with(Path("/path/to/config3.yaml"), False)
    mock_check_leafs.assert_not_called()
    mock_yaml_load.assert_not_called()


def test_get_config_file_modified(
    mock_stat, mock_check_permissions, mock_check_leafs, mock_open, mock_yaml_load
):
    mock_stat.return_value.st_mtime = 12346.0
    config_instance = Config(Path("/path/to/config4.yaml"))
    config_instance._last_modified_time = 12345.0

    mock_yaml_load.return_value = {"modified": "config"}

    config = config_instance.get_config()
    assert config == {"modified": "config"}

    mock_check_permissions.assert_called_once_with(Path("/path/to/config4.yaml"), False)
    mock_check_leafs.assert_called_once()
    mock_yaml_load.assert_called_once()


def test_get_config_os_error_cached_config(
    mock_stat, mock_check_permissions, mock_check_leafs, mock_yaml_load
):
    mock_stat.return_value.st_mtime = 12345.0
    config_instance = Config(Path("/path/to/config5.yaml"))

    # Simulate an OSError and ensure that the cached configuration is returned
    mock_check_permissions.side_effect = OSError
    config_instance._config = {"cached": "config"}

    config = config_instance.get_config()

    assert config == {"cached": "config"}
    mock_check_permissions.assert_called_once_with(Path("/path/to/config5.yaml"), False)
    mock_check_leafs.assert_not_called()
    mock_yaml_load.assert_not_called()
