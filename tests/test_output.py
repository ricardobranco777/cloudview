# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name,protected-access

import json

import pytest

from cloudview.instance import Instance
from cloudview.output import Output


@pytest.fixture
def text_output():
    return Output(type="text", keys=["name", "age"])


@pytest.fixture
def json_output():
    return Output(type="json")


# Use the "monkeypatch" fixture to reset the singleton instance before each test
@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    monkeypatch.setattr(Output, "_singleton_instance", None)


def test_invalid_output_type():
    with pytest.raises(ValueError, match="Invalid type: invalid_type"):
        Output(type="invalid_type")


def test_text_output_header(text_output, capsys):
    expected_header = "NAME  AGE\n"
    text_output.header()
    captured = capsys.readouterr()
    assert captured.out == expected_header


def test_text_output_info(text_output, capsys):
    expected_info = "John  30\n"
    text_output.info({"name": "John", "age": 30})
    captured = capsys.readouterr()
    assert captured.out == expected_info


def test_json_output_dict(json_output, capsys):
    json_output.header()
    info = {"name": "John", "age": 30}
    json_output.info(info)
    json_output.footer()
    captured = capsys.readouterr()
    assert [info] == json.loads(captured.out)


def test_json_output_obj(json_output, capsys):
    json_output.header()
    info = Instance(
        name="instance-1",
        provider="P",
        cloud="C",
        id="id",
        size="s",
        time="T",
        state="S",
        location="L",
        extra={},
    )
    json_output.info(info)
    json_output.footer()
    captured = capsys.readouterr()
    assert [info.__dict__] == json.loads(captured.out)
