from typing import Any, Iterable
from unittest.mock import MagicMock


def spy_decorator(method):
    mock = MagicMock()

    async def wrapper(*args, **kwargs):
        mock(*args, **kwargs)
        return await method(*args, **kwargs)

    wrapper.mock = mock
    return wrapper


class AsyncIterator:
    def __init__(self, iterable: Iterable[Any]) -> None:
        self.iter = iter(iterable)

    def __aiter__(self):
        return self

    async def __anext__(self):
        return next(self.iter)
