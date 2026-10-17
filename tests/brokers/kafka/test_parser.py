import pytest

from faststream.kafka import ConsumerRecord
from faststream.kafka.message import KafkaMessage
from faststream.kafka.parser import AioKafkaBatchParser, AioKafkaParser
from tests.brokers.base.parser import CustomParserTestcase

from .basic import KafkaTestcaseConfig


@pytest.mark.kafka()
@pytest.mark.connected()
class TestCustomParser(KafkaTestcaseConfig, CustomParserTestcase):
    pass


def make_message(headers: list[tuple[str, bytes | None]]) -> ConsumerRecord[None, bytes]:
    return ConsumerRecord(
        topic="test-topic",
        partition=0,
        offset=0,
        timestamp=0,
        timestamp_type=0,
        key=None,
        value=b'{"value": 1}',
        checksum=None,
        serialized_key_size=0,
        serialized_value_size=12,
        headers=headers,
    )


@pytest.mark.kafka()
@pytest.mark.asyncio()
async def test_parse_non_utf8_headers() -> None:
    """Fixes https://github.com/ag2ai/faststream/issues/2458."""
    parser = AioKafkaParser(msg_class=KafkaMessage, regex=None)
    result = await parser.parse_message(
        make_message([
            ("text", "привет".encode()),
            ("binary", b"\xc3\x28"),
            ("empty", b""),
            ("nullable", None),
            ("reply_to", b"reply-\xff"),
            ("content-type", b"type-\xff"),
            ("correlation_id", b"id-\xff"),
        ])
    )

    assert (
        result.headers,
        result.reply_to,
        result.content_type,
        result.correlation_id,
    ) == (
        {
            "text": "привет",
            "binary": "\ufffd(",
            "empty": "",
            "reply_to": "reply-\ufffd",
            "content-type": "type-\ufffd",
            "correlation_id": "id-\ufffd",
        },
        "reply-\ufffd",
        "type-\ufffd",
        "id-\ufffd",
    )


@pytest.mark.kafka()
@pytest.mark.asyncio()
async def test_parse_batch_non_utf8_headers() -> None:
    """Fixes https://github.com/ag2ai/faststream/issues/2458."""
    parser = AioKafkaBatchParser(msg_class=KafkaMessage, regex=None)
    result = await parser.parse_batch((
        make_message([("content-type", b"application/json"), ("text", b"first")]),
        make_message([
            ("content-type", b"application/json"),
            ("binary", b"\xc3\x28"),
            ("nullable", None),
        ]),
    ))

    assert (result.headers, result.batch_headers, await parser.decode_batch(result)) == (
        {"content-type": "application/json", "text": "first"},
        [
            {"content-type": "application/json", "text": "first"},
            {"content-type": "application/json", "binary": "\ufffd("},
        ],
        [{"value": 1}, {"value": 1}],
    )
