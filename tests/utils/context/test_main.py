import pytest
from pydantic import ValidationError

from faststream.utils import Context, ContextRepo, apply_types


def test_context_getattr(context: ContextRepo):
    a = 1000
    context.set_global("key", a)

    assert context.key is a
    assert context.key2 is None


@pytest.mark.asyncio
async def test_context_apply(context: ContextRepo):
    a = 1000
    context.set_global("key", a)

    @apply_types
    async def use(key=Context()):
        return key is a

    assert await use()


@pytest.mark.asyncio
async def test_context_ignore(context: ContextRepo):
    a = 3
    context.set_global("key", a)

    @apply_types
    async def use():
        return None

    assert await use() is None


@pytest.mark.asyncio
async def test_context_apply_multi(context: ContextRepo):
    a = 1001
    context.set_global("key_a", a)

    b = 1000
    context.set_global("key_b", b)

    @apply_types
    async def use1(key_a=Context()):
        return key_a is a

    assert await use1()

    @apply_types
    async def use2(key_b=Context()):
        return key_b is b

    assert await use2()

    @apply_types
    async def use3(key_a=Context(), key_b=Context()):
        return key_a is a and key_b is b

    assert await use3()


@pytest.mark.asyncio
async def test_context_overrides(context: ContextRepo):
    a = 1001
    context.set_global("test", a)

    b = 1000
    context.set_global("test", b)

    @apply_types
    async def use(test=Context()):
        return test is b

    assert await use()


@pytest.mark.asyncio
async def test_context_nested_apply(context: ContextRepo):
    a = 1000
    context.set_global("key", a)

    @apply_types
    def use_nested(key=Context()):
        return key

    @apply_types
    async def use(key=Context()):
        return key is use_nested() is a

    assert await use()


@pytest.mark.asyncio
async def test_reset_global(context: ContextRepo):
    a = 1000
    context.set_global("key", a)
    context.reset_global("key")

    @apply_types
    async def use(key=Context()): ...

    with pytest.raises(ValidationError):
        await use()


@pytest.mark.asyncio
async def test_clear_context(context: ContextRepo):
    a = 1000
    context.set_global("key", a)
    context.clear()

    @apply_types
    async def use(key=Context(default=None)):
        return key is None

    assert await use()


def test_scope(context: ContextRepo):
    @apply_types
    def use(key=Context(), key2=Context()):
        assert key == 1
        assert key2 == 1

    with context.scope("key", 1), context.scope("key2", 1):
        use()

    assert context.get("key") is None
    assert context.get("key2") is None


def test_default(context: ContextRepo):
    @apply_types
    def use(
        key=Context(),
        key2=Context(),
        key3=Context(default=1),
        key4=Context("key.key4", default=1),
        key5=Context("key5.key6"),
    ):
        assert key == 0
        assert key2 is True
        assert key3 == 1
        assert key4 == 1
        assert key5 is False

    with context.scope("key", 0), context.scope("key2", True), context.scope(
        "key5", {"key6": False}
    ):
        use()


def test_initial():
    @apply_types
    def use(
        a,
        key=Context(initial=list),
    ):
        key.append(a)
        return key

    assert use(1) == [1]
    assert use(2) == [1, 2]
