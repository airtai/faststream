from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Optional,
    Union,
)

from aiokafka import ConsumerRecord
from typing_extensions import Doc, override

from faststream._internal.publisher.usecase import PublisherUsecase
from faststream._internal.types import MsgType
from faststream.kafka.message import KafkaMessage
from faststream.kafka.response import KafkaPublishCommand
from faststream.message import gen_cor_id
from faststream.response.publish_type import PublishType

if TYPE_CHECKING:
    from faststream._internal.basic_types import SendableMessage
    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware
    from faststream.kafka.message import KafkaMessage
    from faststream.kafka.publisher.producer import AioKafkaFastProducer
    from faststream.response.response import PublishCommand


class LogicPublisher(PublisherUsecase[MsgType]):
    """A class to publish messages to a Kafka topic."""

    _producer: Optional["AioKafkaFastProducer"]

    def __init__(
        self,
        *,
        topic: str,
        partition: Optional[int],
        headers: Optional[dict[str, str]],
        reply_to: str,
        # Publisher args
        broker_middlewares: Iterable["BrokerMiddleware[MsgType]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            # AsyncAPI args
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.topic = topic
        self.partition = partition
        self.reply_to = reply_to
        self.headers = headers or {}

        self._producer = None

    def add_prefix(self, prefix: str) -> None:
        self.topic = f"{prefix}{self.topic}"

    @override
    async def request(
        self,
        message: Annotated[
            "SendableMessage",
            Doc("Message body to send."),
        ],
        topic: Annotated[
            str,
            Doc("Topic where the message will be published."),
        ] = "",
        *,
        key: Annotated[
            Union[bytes, Any, None],
            Doc(
                """
            A key to associate with the message. Can be used to
            determine which partition to send the message to. If partition
            is `None` (and producer's partitioner config is left as default),
            then messages with the same key will be delivered to the same
            partition (but if key is `None`, partition is chosen randomly).
            Must be type `bytes`, or be serializable to bytes via configured
            `key_serializer`.
            """,
            ),
        ] = None,
        partition: Annotated[
            Optional[int],
            Doc(
                """
            Specify a partition. If not set, the partition will be
            selected using the configured `partitioner`.
            """,
            ),
        ] = None,
        timestamp_ms: Annotated[
            Optional[int],
            Doc(
                """
            Epoch milliseconds (from Jan 1 1970 UTC) to use as
            the message timestamp. Defaults to current time.
            """,
            ),
        ] = None,
        headers: Annotated[
            Optional[dict[str, str]],
            Doc("Message headers to store metainformation."),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        timeout: Annotated[
            float,
            Doc("Timeout to send RPC request."),
        ] = 0.5,
    ) -> "KafkaMessage":
        cmd = KafkaPublishCommand(
            message,
            topic=topic or self.topic,
            key=key,
            partition=partition or self.partition,
            headers=self.headers | (headers or {}),
            correlation_id=correlation_id or gen_cor_id(),
            timestamp_ms=timestamp_ms,
            timeout=timeout,
            _publish_type=PublishType.Request,
        )

        msg: KafkaMessage = await self._basic_request(cmd)
        return msg


class DefaultPublisher(LogicPublisher[ConsumerRecord]):
    def __init__(
        self,
        *,
        key: Union[bytes, str, None],
        topic: str,
        partition: Optional[int],
        headers: Optional[dict[str, str]],
        reply_to: str,
        # Publisher args
        broker_middlewares: Iterable["BrokerMiddleware[ConsumerRecord]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            topic=topic,
            partition=partition,
            reply_to=reply_to,
            headers=headers,
            # publisher args
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            # AsyncAPI args
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.key = key

    @override
    async def publish(
        self,
        message: Annotated[
            "SendableMessage",
            Doc("Message body to send."),
        ],
        topic: Annotated[
            str,
            Doc("Topic where the message will be published."),
        ] = "",
        *,
        key: Annotated[
            Union[bytes, Any, None],
            Doc(
                """
            A key to associate with the message. Can be used to
            determine which partition to send the message to. If partition
            is `None` (and producer's partitioner config is left as default),
            then messages with the same key will be delivered to the same
            partition (but if key is `None`, partition is chosen randomly).
            Must be type `bytes`, or be serializable to bytes via configured
            `key_serializer`.
            """,
            ),
        ] = None,
        partition: Annotated[
            Optional[int],
            Doc(
                """
            Specify a partition. If not set, the partition will be
            selected using the configured `partitioner`.
            """,
            ),
        ] = None,
        timestamp_ms: Annotated[
            Optional[int],
            Doc(
                """
            Epoch milliseconds (from Jan 1 1970 UTC) to use as
            the message timestamp. Defaults to current time.
            """,
            ),
        ] = None,
        headers: Annotated[
            Optional[dict[str, str]],
            Doc("Message headers to store metainformation."),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("Reply message topic name to send response."),
        ] = "",
        no_confirm: Annotated[
            bool,
            Doc("Do not wait for Kafka publish confirmation."),
        ] = False,
    ) -> None:
        cmd = KafkaPublishCommand(
            message,
            topic=topic or self.topic,
            key=key or self.key,
            partition=partition or self.partition,
            reply_to=reply_to or self.reply_to,
            headers=self.headers | (headers or {}),
            correlation_id=correlation_id or gen_cor_id(),
            timestamp_ms=timestamp_ms,
            no_confirm=no_confirm,
            _publish_type=PublishType.Publish,
        )
        await self._basic_publish(cmd, _extra_middlewares=())

    @override
    async def _publish(
        self,
        cmd: Union["PublishCommand", "KafkaPublishCommand"],
        *,
        _extra_middlewares: Iterable["PublisherMiddleware"],
    ) -> None:
        """This method should be called in subscriber flow only."""
        cmd = KafkaPublishCommand.from_cmd(cmd)

        cmd.destination = self.topic

        cmd.headers = self.headers | cmd.headers
        cmd.reply_to = cmd.reply_to or self.reply_to
        cmd.partition = cmd.partition or self.partition
        cmd.key = cmd.key or self.key

        await self._basic_publish(cmd, _extra_middlewares=_extra_middlewares)

    @override
    async def request(
        self,
        message: Annotated[
            "SendableMessage",
            Doc("Message body to send."),
        ],
        topic: Annotated[
            str,
            Doc("Topic where the message will be published."),
        ] = "",
        *,
        key: Annotated[
            Union[bytes, Any, None],
            Doc(
                """
            A key to associate with the message. Can be used to
            determine which partition to send the message to. If partition
            is `None` (and producer's partitioner config is left as default),
            then messages with the same key will be delivered to the same
            partition (but if key is `None`, partition is chosen randomly).
            Must be type `bytes`, or be serializable to bytes via configured
            `key_serializer`.
            """,
            ),
        ] = None,
        partition: Annotated[
            Optional[int],
            Doc(
                """
            Specify a partition. If not set, the partition will be
            selected using the configured `partitioner`.
            """,
            ),
        ] = None,
        timestamp_ms: Annotated[
            Optional[int],
            Doc(
                """
            Epoch milliseconds (from Jan 1 1970 UTC) to use as
            the message timestamp. Defaults to current time.
            """,
            ),
        ] = None,
        headers: Annotated[
            Optional[dict[str, str]],
            Doc("Message headers to store metainformation."),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        timeout: Annotated[
            float,
            Doc("Timeout to send RPC request."),
        ] = 0.5,
    ) -> "KafkaMessage":
        return await super().request(
            message,
            topic=topic,
            key=key or self.key,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=headers,
            correlation_id=correlation_id,
            timeout=timeout,
        )


class BatchPublisher(LogicPublisher[tuple["ConsumerRecord", ...]]):
    @override
    async def publish(
        self,
        *messages: Annotated[
            "SendableMessage",
            Doc("Messages bodies to send."),
        ],
        topic: Annotated[
            str,
            Doc("Topic where the message will be published."),
        ] = "",
        partition: Annotated[
            Optional[int],
            Doc(
                """
            Specify a partition. If not set, the partition will be
            selected using the configured `partitioner`.
            """,
            ),
        ] = None,
        timestamp_ms: Annotated[
            Optional[int],
            Doc(
                """
            Epoch milliseconds (from Jan 1 1970 UTC) to use as
            the message timestamp. Defaults to current time.
            """,
            ),
        ] = None,
        headers: Annotated[
            Optional[dict[str, str]],
            Doc("Messages headers to store metainformation."),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("Reply message topic name to send response."),
        ] = "",
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        no_confirm: Annotated[
            bool,
            Doc("Do not wait for Kafka publish confirmation."),
        ] = False,
    ) -> None:
        cmd = KafkaPublishCommand(
            *messages,
            key=None,
            topic=topic or self.topic,
            partition=partition or self.partition,
            reply_to=reply_to or self.reply_to,
            headers=self.headers | (headers or {}),
            correlation_id=correlation_id or gen_cor_id(),
            timestamp_ms=timestamp_ms,
            no_confirm=no_confirm,
            _publish_type=PublishType.Publish,
        )

        await self._basic_publish_batch(cmd, _extra_middlewares=())

    @override
    async def _publish(
        self,
        cmd: Union["PublishCommand", "KafkaPublishCommand"],
        *,
        _extra_middlewares: Iterable["PublisherMiddleware"],
    ) -> None:
        """This method should be called in subscriber flow only."""
        cmd = KafkaPublishCommand.from_cmd(cmd, batch=True)

        cmd.destination = self.topic

        cmd.headers = self.headers | cmd.headers
        cmd.reply_to = cmd.reply_to or self.reply_to
        cmd.partition = cmd.partition or self.partition

        await self._basic_publish_batch(cmd, _extra_middlewares=_extra_middlewares)
