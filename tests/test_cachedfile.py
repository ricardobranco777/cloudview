# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name

import pytest
from cloudview.cachedfile import CachedFile


@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    monkeypatch.setattr(CachedFile, "_singleton_instances", {})


def test_cached_file_singleton(mocker):
    mocker.patch("builtins.open")
    instance1 = CachedFile("test_file.txt")
    instance2 = CachedFile("test_file.txt")
    assert instance1 is instance2


def test_cached_file_read_data(mocker):
    mock_open = mocker.mock_open(read_data="Mock data")
    mocker.patch("builtins.open", mock_open)

    cached_file = CachedFile("test_file.txt")
    data = cached_file.get_data()

    assert data == "Mock data"
    mock_open.assert_called_once_with("test_file.txt", encoding="utf-8")


def test_cached_file_read_data_only_once(mocker):
    mock_open = mocker.mock_open(read_data="Mock data")
    mocker.patch("builtins.open", mock_open)

    cached_file = CachedFile("test_file.txt")
    data1 = cached_file.get_data()
    data2 = cached_file.get_data()

    assert data1 == data2
    mock_open.assert_called_once_with("test_file.txt", encoding="utf-8")


def test_cached_file_data_updated(mocker):
    mock_open = mocker.mock_open(read_data="New data")
    mocker.patch("builtins.open", mock_open)

    cached_file = CachedFile("test_file.txt")
    initial_data = cached_file.get_data()

    mocker.patch("os.stat").return_value.st_mtime = 1234567890
    mock_open = mocker.mock_open(read_data="Updated data")
    mocker.patch("builtins.open", mock_open)

    updated_data = cached_file.get_data()

    assert updated_data == "Updated data"
    assert initial_data != updated_data
    mock_open.assert_called_once_with("test_file.txt", encoding="utf-8")


def test_cached_file_handle_file_error(mocker, caplog):
    mock_open = mocker.mock_open(read_data="Cached data")
    mocker.patch("builtins.open", mock_open)
    mock_stat = mocker.patch("os.stat")
    mock_stat.side_effect = OSError("File not found")

    cached_file = CachedFile("removed_file.txt")
    data = cached_file.get_data()

    assert data == "Cached data"
    mock_open.assert_called_once_with("removed_file.txt", encoding="utf-8")
    mock_stat.assert_called_once_with("removed_file.txt")

    # Check if the expected log message was emitted
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert "removed_file.txt" in caplog.records[0].message
