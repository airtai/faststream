from faststream.utils.classes import Singleton


def test_singleton():
    assert Singleton() is Singleton()


def test_drop():
    s1 = Singleton()
    s1._drop()
    assert Singleton() is not s1
