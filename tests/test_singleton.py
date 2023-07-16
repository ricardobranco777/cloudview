from cloudview.singleton import Singleton


def test_singleton_decorator():
    @Singleton
    class SingletonClass:
        def __init__(self, name):
            self.name = name

    obj1 = SingletonClass("Object 1")
    obj2 = SingletonClass("Object 2")

    assert obj1 is not obj2
    assert obj1.name == "Object 1"
    assert obj2.name == "Object 2"


def test_singleton_decorator_with_arguments():
    @Singleton
    class SingletonClassWithArgs:
        def __init__(self, name, age):
            self.name = name
            self.age = age

    obj1 = SingletonClassWithArgs("Object 1", age=20)
    obj2 = SingletonClassWithArgs("Object 1", age=20)
    obj3 = SingletonClassWithArgs("Object 2", age=20)

    assert obj1 is obj2
    assert obj1 is not obj3
