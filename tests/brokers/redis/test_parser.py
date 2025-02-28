import json

import pytest

from faststream.redis import RedisBroker
from faststream.redis.parser import RawMessage
from tests.brokers.base.parser import CustomParserTestcase


@pytest.mark.redis
class TestCustomParser(CustomParserTestcase):
    broker_class = RedisBroker


@pytest.mark.parametrize(
    ("data", "expected_data"),
    [
        (
            {"id": "12345678" * 4, "date": "2021-01-01T00:00:00Z"},
            json.dumps({"id": "12345678" * 4, "date": "2021-01-01T00:00:00Z"}).encode(),
        ),
        (
            # this is not utf-8 compatible
            b"\x82\xa2",
            b"\x82\xa2",
        ),
        (True, b"true"),
        ([True, False, True], b"[true, false, true]"),
    ],
)
@pytest.mark.redis
def test_raw_message(
    data,
    expected_data,
):
    msg_bytes = RawMessage.encode(
        message=data, reply_to=None, headers=None, correlation_id="cor_id"
    )

    raw_data_result, _ = RawMessage.parse(msg_bytes)

    assert raw_data_result == expected_data
