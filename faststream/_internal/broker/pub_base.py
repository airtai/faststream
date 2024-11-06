from abc import abstractmethod
from collections.abc import Iterable
from functools import partial
from typing import TYPE_CHECKING, Any, Generic, Optional

from faststream._internal.subscriber.utils import process_msg
from faststream._internal.types import MsgType
from faststream.message.source_type import SourceType

if TYPE_CHECKING:
    from faststream._internal.basic_types import SendableMessage
    from faststream._internal.context import ContextRepo
    from faststream._internal.publisher.proto import ProducerProto
    from faststream._internal.types import BrokerMiddleware
    from faststream.response import PublishCommand


class BrokerPublishMixin(Generic[MsgType]):
    middlewares: Iterable["BrokerMiddleware[MsgType]"]
    context: "ContextRepo"

    @abstractmethod
    async def publish(
        self,
        message: "SendableMessage",
        queue: str,
        /,
    ) -> None:
        raise NotImplementedError

    async def _basic_publish(
        self,
        cmd: "PublishCommand",
        *,
        producer: "ProducerProto",
    ) -> Optional[Any]:
        publish = producer.publish

        for m in self.middlewares:
            publish = partial(m(None, context=self.context).publish_scope, publish)

        return await publish(cmd)

    @abstractmethod
    async def publish_batch(
        self,
        *messages: "SendableMessage",
        queue: str,
    ) -> None:
        raise NotImplementedError

    async def _basic_publish_batch(
        self,
        cmd: "PublishCommand",
        *,
        producer: "ProducerProto",
    ) -> None:
        publish = producer.publish_batch

        for m in self.middlewares:
            publish = partial(m(None, context=self.context).publish_scope, publish)

        await publish(cmd)

    @abstractmethod
    async def request(
        self,
        message: "SendableMessage",
        queue: str,
        /,
        timeout: float = 0.5,
    ) -> Any:
        raise NotImplementedError

    async def _basic_request(
        self,
        cmd: "PublishCommand",
        *,
        producer: "ProducerProto",
    ) -> Any:
        request = producer.request

        for m in self.middlewares:
            request = partial(m(None, context=self.context).publish_scope, request)

        published_msg = await request(cmd)

        response_msg: Any = await process_msg(
            msg=published_msg,
            middlewares=(
                m(published_msg, context=self.context) for m in self.middlewares
            ),
            parser=producer._parser,
            decoder=producer._decoder,
            source_type=SourceType.RESPONSE,
        )
        return response_msg
