# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,no-member
import pytest
from cloudview.instance import Instance


def test_instance_creation():
    instance = Instance(name="Example", type="VM", status="Running")
    assert instance.name == "Example"
    assert instance.type == "VM"
    assert instance.status == "Running"


def test_instance_dict_access():
    instance = Instance(name="Example", type="VM", status="Running")

    assert instance["name"] == "Example"
    assert instance["type"] == "VM"
    assert instance["status"] == "Running"


def test_instance_dict_assignment():
    instance = Instance()

    instance["name"] = "Updated Name"
    instance["type"] = "Updated Type"

    assert instance.name == "Updated Name"
    assert instance.type == "Updated Type"


def test_instance_unknown_attribute():
    instance = Instance()
    with pytest.raises(AttributeError):
        _ = instance["unknown_attribute"]
