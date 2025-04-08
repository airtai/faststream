from typing import TYPE_CHECKING, Dict, cast

if TYPE_CHECKING:
    import aio_pika

    from faststream.rabbit.schemas import Channel


class ChannelManager:
    __slots__ = ("__channels", "__connection")

    def __init__(self, connection: "aio_pika.RobustConnection") -> None:
        self.__connection = connection
        self.__channels: Dict[int, aio_pika.RobustChannel] = {}

    async def get_channel(
        self,
        channel: "Channel",
    ) -> "aio_pika.RobustChannel":
        """Declare a queue."""
        hash_key = id(channel)

        if (ch := self.__channels.get(hash_key)) is None:
            self.__channels[hash_key] = ch = cast(
                "aio_pika.RobustChannel",
                await self.__connection.channel(
                    channel_number=channel.channel_number,
                    publisher_confirms=channel.publisher_confirms,
                    on_return_raises=channel.on_return_raises,
                ),
            )

            if channel.prefetch_count:
                await ch.set_qos(prefetch_count=channel.prefetch_count)

        return ch
