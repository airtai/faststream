import pytest

from faststream.utils.ast import is_contains_context_name


class Context:
    def __enter__(self) -> "Context":
        return self

    def __exit__(self, *args):
        pass

    async def __aenter__(self) -> "Context":
        return self

    async def __aexit__(self, *args):
        pass


class A(Context):
    def __init__(self):
        self.contains = is_contains_context_name(self.__class__.__name__, B.__name__)


class B(Context):
    def __init__(self):
        pass


def test_base():
    with A() as a, B():
        assert a.contains


@pytest.mark.asyncio
async def test_base_async():
    async with A() as a, B():
        assert a.contains


def test_nested():
    with A() as a, B():
        assert a.contains


@pytest.mark.asyncio
async def test_nested_async():
    async with A() as a, B():
        assert a.contains


@pytest.mark.asyncio
async def test_async_A():  # noqa: N802
    async with A() as a:
        with B():
            assert a.contains


@pytest.mark.asyncio
async def test_async_B():  # noqa: N802
    with A() as a:
        async with B():
            assert a.contains


def test_base_invalid():
    with B(), B(), A() as a:
        assert not a.contains


def test_nested_invalid():
    with B(), A() as a:
        assert not a.contains


def test_not_broken():
    with A() as a, B():
        assert a.contains

        # test ast processes another context correctly
        with pytest.raises(ValueError):  # noqa: PT011
            raise ValueError()
