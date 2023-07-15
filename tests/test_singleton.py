import pytest

from cloudview.singleton import Singleton, Singleton2


def test_singleton_decorator():
    @Singleton
    class SingletonClass:
        def __init__(self, name):
            self.name = name

    obj1 = SingletonClass("Object 1")
    obj2 = SingletonClass("Object 2")

    assert obj1 is obj2
    assert obj1.name == obj2.name


def test_singleton2_decorator():
    @Singleton2
    class Singleton2Class:
        def __init__(self, name):
            self.name = name

    obj1 = Singleton2Class("Object 1")
    obj2 = Singleton2Class("Object 2")

    assert obj1 is not obj2
    assert obj1.name == "Object 1"
    assert obj2.name == "Object 2"


def test_singleton2_decorator_with_arguments():
    @Singleton2
    class Singleton2ClassWithArgs:
        def __init__(self, name, age):
            self.name = name
            self.age = age

    obj1 = Singleton2ClassWithArgs("Object 1", age=20)
    obj2 = Singleton2ClassWithArgs("Object 1", age=20)
    obj3 = Singleton2ClassWithArgs("Object 2", age=20)

    assert obj1 is obj2
    assert obj1 is not obj3


if __name__ == "__main__":
    pytest.main()
