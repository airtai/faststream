import json

import pytest
from msgpack import packb
from pydantic import BaseModel

from faststream.redis import RedisBroker
from faststream.redis.parser import RawMessage
from tests.brokers.base.parser import CustomParserTestcase


class M(BaseModel):
    a: str


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
            packb({"id": "12345678" * 4, "date": "2021-01-01T00:00:00Z"}),
            packb({"id": "12345678" * 4, "date": "2021-01-01T00:00:00Z"}),
        ),
        (True, b"true"),
        ([True, False, True], b"[true, false, true]"),
        (M(a="test"), json.dumps({"a": "test"}).encode()),
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
