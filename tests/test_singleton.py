# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring

from cloudview.singleton import Singleton, Singleton2


def test_singleton():
    class Example(metaclass=Singleton):
        def __init__(self, value):
            self.value = value

    instance1 = Example("first instance")
    instance2 = Example("second instance")

    assert instance1 is instance2
    assert instance1.value == instance2.value


def test_singleton2():
    class Example(metaclass=Singleton2):
        def __init__(self, value):
            self.value = value

    instance1 = Example("first instance")
    instance2 = Example("first instance")
    instance3 = Example("second instance")

    assert instance1 is instance2
    assert instance1 is not instance3
    assert instance1.value == instance2.value
    assert instance1.value != instance3.value
