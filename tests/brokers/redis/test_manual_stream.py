import anyio
import pytest

from faststream.redis import RedisBroker, RedisStreamMessage, StreamSub


@pytest.mark.connected()
@pytest.mark.redis()
@pytest.mark.asyncio()
@pytest.mark.parametrize("no_ack", (False, True))
@pytest.mark.parametrize("iterate", (False, True))
async def test_manual_stream_read_respects_no_ack(
    queue: str,
    no_ack: bool,
    iterate: bool,
) -> None:
    broker = RedisBroker()
    subscriber = broker.subscriber(
        stream=StreamSub(queue, group=queue, consumer="reader", no_ack=no_ack),
    )

    async with broker:
        await broker.start()
        await broker.publish("hello", stream=queue)

        message: RedisStreamMessage | None
        if iterate:
            with anyio.fail_after(3):
                message = await anext(aiter(subscriber))
        else:
            message = await subscriber.get_one(timeout=3)

        assert message is not None
        assert await message.decode() == "hello"
        client = await broker.connect()
        pending = await client.xpending(queue, queue)  # type: ignore[no-untyped-call]
        assert pending["pending"] == (0 if no_ack else 1)
