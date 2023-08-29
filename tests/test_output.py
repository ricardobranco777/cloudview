# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name

import json

import pytest

from cloudview.instance import Instance
from cloudview.output import Output


@pytest.fixture
def text_output():
    return Output(type="text", format="{item[name]}  {item[age]}")


@pytest.fixture
def json_output():
    return Output(type="json")


@pytest.fixture
def html_output():
    return Output(type="html", keys=["name", "age", "href"], format="<tr>{lines}</tr>")


# Use the "monkeypatch" fixture to reset the singleton instance before each test
@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch):
    monkeypatch.setattr(Output, "_singleton_instance", None)


def test_invalid_output_type():
    with pytest.raises(ValueError, match="Invalid type: invalid_type"):
        Output(type="invalid_type")


def test_text_output_header(text_output, capsys):
    expected_header = "NAME  AGE\n"
    text_output.keys = ["name", "age"]
    text_output.header()
    captured = capsys.readouterr()
    assert captured.out == expected_header


def test_text_output_info(text_output, capsys):
    expected_info = "John   30\n"
    text_output.format = "{item[name]}   {item[age]}"
    text_output.info({"name": "John", "age": 30})
    captured = capsys.readouterr()
    assert captured.out == expected_info


def test_html_output_header(html_output, capsys):
    expected_header = "<th>NAME</th><th>AGE</th><th>HREF</th>\n"
    html_output.header()
    captured = capsys.readouterr()
    assert expected_header in captured.out


def test_html_output_info(html_output, capsys):
    expected_info = '<tr>\n <td><a href="john.html">John</a></td> <td>30</td> <td>john.html</td>\n</tr>\n'
    item = {"name": "John", "age": 30, "href": "john.html"}
    html_output.info(item)
    captured = capsys.readouterr()
    assert expected_info in captured.out


def test_html_output_footer(html_output, capsys):
    html_output.footer()
    captured = capsys.readouterr()
    assert "</html>" in captured.out


def test_json_output_dict(json_output, capsys):
    json_output.header()
    info = {"name": "John", "age": 30}
    json_output.info(info)
    json_output.footer()
    captured = capsys.readouterr()
    assert [info] == json.loads(captured.out)


def test_json_output_obj(json_output, capsys):
    json_output.header()
    info = Instance(name="instance-1", age="30")
    json_output.info(info)
    json_output.footer()
    captured = capsys.readouterr()
    assert [info.__dict__] == json.loads(captured.out)
