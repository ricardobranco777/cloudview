# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,no-member,eval-used,too-few-public-methods
import pytest
from cloudview.instance import Instance, CSP


def test_instance_repr():
    item = Instance(
        name="Example",
        provider="P",
        cloud="C",
        id="id",
        size="s",
        time="T",
        state="Running",
        location="L",
        extra={},
    )
    repr_string = repr(item)
    recreated_item = eval(repr_string)
    assert item.__dict__ == recreated_item.__dict__


def test_instance_creation():
    instance = Instance(
        name="Example",
        provider="P",
        cloud="C",
        id="id",
        size="s",
        time="T",
        state="Running",
        location="L",
        extra={},
    )
    assert instance.name == "Example"
    assert instance.state == "Running"


def test_instance_unknown_attribute():
    instance = Instance(
        name="name",
        provider="P",
        cloud="C",
        id="id",
        size="s",
        time="T",
        state="S",
        location="L",
        extra={},
    )
    with pytest.raises(AttributeError):
        _ = instance.unknown_attribute


class MockCSP(CSP):
    def _get_instances(self):
        return [
            Instance(
                id="id1",
                name="Instance1",
                extra={"status": "running"},
                provider="P",
                cloud="C",
                size="s",
                time="T",
                state="S",
                location="L",
            ),
            Instance(
                id="id2",
                name="Instance2",
                extra={"status": "stopped"},
                provider="P",
                cloud="C",
                size="s",
                time="T",
                state="S",
                location="L",
            ),
        ]


def test_csp_creation():
    csp = MockCSP(cloud="MyCloud")
    assert csp.cloud == "MyCloud"


def test_csp_get_instances():
    csp = MockCSP()
    instances = csp.get_instances()
    assert len(instances) == 2
    assert instances[0].name == "Instance1"
    assert instances[1].id == "id2"
