import pytest

from faststream.utils.classes import Singleton, nullcontext


def test_singleton():
    assert Singleton() is Singleton()


def test_drop():
    s1 = Singleton()
    s1._drop()
    assert Singleton() is not s1


@pytest.mark.asyncio
async def test_nullcontext():
    with nullcontext("foo") as context:
        assert context == "foo"
    async with nullcontext("foo") as context:
        assert context == "foo"
