import pytest

from faststream.redis import StreamSub


def test_stream_group():
    with pytest.raises(ValueError):
        StreamSub("test", group="group")

    with pytest.raises(ValueError):
        StreamSub("test", consumer="consumer")

    StreamSub("test", group="group", consumer="consumer")
