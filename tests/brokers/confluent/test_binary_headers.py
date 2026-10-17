from itertools import starmap

import pytest

from faststream.confluent import KafkaBroker, KafkaMessage, KafkaResponse, TestKafkaBroker

pytestmark = [pytest.mark.confluent(), pytest.mark.asyncio()]

INPUT_HEADERS: dict[str, str | bytes | None] = {
    "text": "plain",
    "utf8": "привет".encode(),
    "binary": b"\xc3\x28",
    "empty": b"",
    "nullable": None,
}
DECODED_HEADERS = {
    "text": "plain",
    "utf8": "привет",
    "binary": "\ufffd(",
    "empty": "",
}
RAW_HEADERS = {
    "text": b"plain",
    "utf8": "привет".encode(),
    "binary": b"\xc3\x28",
    "empty": b"",
    "nullable": None,
}
HeaderSnapshot = tuple[dict[str, str], dict[str, bytes | None]]


def _snapshot(
    headers: dict[str, str],
    raw_headers: dict[str, bytes | None],
) -> HeaderSnapshot:
    return (
        {key: value for key, value in headers.items() if key in INPUT_HEADERS},
        {key: value for key, value in raw_headers.items() if key in INPUT_HEADERS},
    )


async def test_publish_binary_headers(queue: str) -> None:
    """Fixes https://github.com/ag2ai/faststream/issues/2214."""
    broker = KafkaBroker()
    received: list[HeaderSnapshot] = []

    @broker.subscriber(queue)
    async def handle(message: KafkaMessage) -> None:
        received.append(_snapshot(message.headers, message.raw_headers))

    async with TestKafkaBroker(broker) as br:
        await br.publish("body", queue, headers=INPUT_HEADERS)

    assert received == [(DECODED_HEADERS, RAW_HEADERS)]


async def test_publish_batch_binary_headers(queue: str) -> None:
    """Fixes https://github.com/ag2ai/faststream/issues/2214."""
    broker = KafkaBroker()
    received: list[tuple[HeaderSnapshot, list[HeaderSnapshot]]] = []

    @broker.subscriber(queue, batch=True)
    async def handle(message: KafkaMessage) -> None:
        received.append((
            _snapshot(message.headers, message.raw_headers),
            list(
                starmap(
                    _snapshot,
                    zip(message.batch_headers, message.batch_raw_headers, strict=True),
                )
            ),
        ))

    async with TestKafkaBroker(broker) as br:
        await br.publish_batch("one", "two", topic=queue, headers=INPUT_HEADERS)

    expected = (DECODED_HEADERS, RAW_HEADERS)
    assert received == [(expected, [expected, expected])]


async def test_request_forwards_binary_response_headers(queue: str) -> None:
    """Fixes https://github.com/ag2ai/faststream/issues/2214."""
    broker = KafkaBroker()

    @broker.subscriber(queue)
    async def handle(message: KafkaMessage) -> KafkaResponse:
        return KafkaResponse(await message.decode(), headers=message.raw_headers)

    async with TestKafkaBroker(broker) as br:
        response = await br.request("body", queue, headers=INPUT_HEADERS)

    assert (
        await response.decode(),
        _snapshot(response.headers, response.raw_headers),
    ) == ("body", (DECODED_HEADERS, RAW_HEADERS))
