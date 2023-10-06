from unittest.mock import MagicMock


def spy_decorator(method):
    mock = MagicMock()

    async def wrapper(*args, **kwargs):
        mock(*args, **kwargs)
        return await method(*args, **kwargs)

    wrapper.mock = mock
    return wrapper
