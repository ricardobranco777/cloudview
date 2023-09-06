# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,no-member
import pytest
from cachetools import cached, TTLCache
from cloudview.instance import Instance, CSP


def test_instance_creation():
    instance = Instance(name="Example", state="Running")
    assert instance.name == "Example"
    assert instance.state == "Running"


def test_instance_dict_access():
    instance = Instance(name="Example", state="Running")

    assert instance["name"] == "Example"
    assert instance["state"] == "Running"


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
                name="Instance1",
                extra={"status": "running"},
            ),
            Instance(
                id="id2",
                name="Instance2",
                extra={"status": "stopped"},
            ),
        ]

    def _get_instance(self, instance_id, params):
        if instance_id == "id1":
            return Instance(
                id="id1",
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
    assert instances[1].id == "id2"


def test_csp_get_instance():
    csp = MockCSP()
    instance = csp.get_instance("id1")
    assert instance["name"] == "Instance1"


def test_csp_get_instance_not_found():
    csp = MockCSP()
    instance = csp.get_instance("unknown_id")
    assert instance is None
