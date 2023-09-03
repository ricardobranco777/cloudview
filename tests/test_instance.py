# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,no-member
import pytest
from cachetools import cached, TTLCache
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


def test_instance_dict_deletion():
    instance = Instance(name="Alice", age=30)

    with pytest.raises(KeyError):
        del instance["nonexistent"]
    del instance["name"]
    with pytest.raises(AttributeError):
        _ = instance.name

    with pytest.raises(KeyError):
        del instance["nonexistent"]


def test_instance_unknown_attribute():
    instance = Instance()
    with pytest.raises(AttributeError):
        _ = instance.unknown_attribute


class MockCSP(CSP):
    @cached(cache=TTLCache(maxsize=1, ttl=300))
    def _get_instances(self):
        return [
            Instance(
                id="id1",
                instance_id="id1",
                name="Instance1",
                extra={"status": "running"},
            ),
            Instance(
                id="id2",
                instance_id="id2",
                name="Instance2",
                extra={"status": "stopped"},
            ),
        ]

    def _get_instance(self, instance_id, params):
        if instance_id == "id1":
            return Instance(
                id="id1",
                instance_id="id1",
                name="Instance1",
                extra={"name=": "Instance1"},
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
    assert instances[1].instance_id == "id2"


def test_csp_get_instance():
    csp = MockCSP()
    instance = csp.get_instance("id1")
    assert instance["name"] == "Instance1"


def test_csp_get_instance_not_found():
    csp = MockCSP()
    instance = csp.get_instance("unknown_id")
    assert instance is None
