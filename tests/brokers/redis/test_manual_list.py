import anyio
import pytest

from faststream.redis import RedisBroker


@pytest.mark.connected()
@pytest.mark.redis()
@pytest.mark.asyncio()
@pytest.mark.parametrize("iterate", (False, True))
async def test_manual_list_read_preserves_empty_messages(
    queue: str,
    iterate: bool,
) -> None:
    broker = RedisBroker()
    subscriber = broker.subscriber(list=queue)

    async with broker:
        await broker.start()
        client = await broker.connect()
        await client.rpush(queue, b"", b"payload")

        received: list[bytes] = []
        if iterate:
            with anyio.fail_after(3):
                async for message in subscriber:
                    received.append(message.body)
                    if len(received) == 2:
                        break
        else:
            for _ in range(2):
                single_message = await subscriber.get_one(timeout=1)
                assert single_message is not None
                received.append(single_message.body)

        assert received == [b"", b"payload"]
        assert await client.llen(queue) == 0
