import pytest

from faststream.redis import StreamSub


def test_stream_group():
    with pytest.raises(ValueError):  # noqa: PT011
        StreamSub("test", group="group")

    with pytest.raises(ValueError):  # noqa: PT011
        StreamSub("test", consumer="consumer")

    StreamSub("test", group="group", consumer="consumer")
