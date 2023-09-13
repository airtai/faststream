from typing import Optional

from faststream import BaseMiddleware, FastStream
from faststream.kafka import KafkaBroker
from faststream.types import DecodedMessage, SendableMessage


class CustomMidlleware(BaseMiddleware):
    async def on_receive(self):
        """call on message received"""
        return await super().on_receive()

    async def after_processed(self, exc_type, exc_val, exec_tb):
        """call in the message processing end"""
        return await super().after_processed(exc_type, exc_val, exec_tb)

    async def on_consume(self, msg: DecodedMessage) -> DecodedMessage:
        """call at message consumed by a handler"""
        return await super().on_consume(msg)

    async def after_consume(self, err: Optional[Exception]) -> None:
        """call after handler function execution"""
        return await super().after_consume(err)

    async def on_publish(self, msg: SendableMessage) -> SendableMessage:
        """call before response message publish"""
        return await super().on_publish(msg)

    async def after_publish(self, err: Optional[Exception]) -> None:
        """call after response message published"""
        return await super().after_publish(err)


broker = KafkaBroker(
    "localhost:9092",
    middlewares=(
        # broker middlewares may implement
        # all methods
        CustomMidlleware,
    ),
)
app = FastStream(broker)


@broker.subscriber(
    "test-topic",
    middlewares=(
        # subscriber/router middlewares should implement
        # `on_consume`, `after_consume`,
        # `on_publish` and `after_publish` methods
        # If they will implement `on_receive` and `after_processed` methods
        # these methods will be called for each handler filter function
        CustomMidlleware,
    ),
)
async def handler():
    pass
