# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,no-member
import pytest
from cloudview.instance import Instance, CSP


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


class MockCSP(CSP):
    def _get_instances(self):
        return [
            Instance(identifier="id1", name="Instance1", extra={"status": "running"}),
            Instance(identifier="id2", name="Instance2", extra={"status": "stopped"}),
        ]

    def _get_instance(self, identifier, params):
        if identifier == "id1":
            return Instance(
                identifier="id1", name="Instance1", extra={"name=": "Instance1"}
            )
        return None


def test_csp_creation():
    csp = MockCSP(cloud="MyCloud")
    assert csp.cloud == "MyCloud"


def test_csp_get_instances():
    csp = MockCSP()
    instances = csp.get_instances()
    assert len(instances) == 2
    assert instances[0].name == "Instance1"
    assert instances[1].identifier == "id2"


def test_csp_get_instance():
    csp = MockCSP()
    instance = csp.get_instance("id1")
    assert instance["status"] == "running"


def test_csp_get_instance_not_found():
    csp = MockCSP()
    instance = csp.get_instance("unknown_id")
    assert instance is None
