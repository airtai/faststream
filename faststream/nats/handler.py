from typing import Any, Callable, Dict, Optional, Sequence, Union

from fast_depends.core import CallModel
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.js import JetStreamContext

from faststream._compat import override
from faststream.broker.handler import AsyncHandler
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.parsers import resolve_custom_func
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.nats.js_stream import JStream
from faststream.nats.message import NatsMessage
from faststream.nats.parser import JsParser, Parser
from faststream.types import AnyDict
from faststream.utils.context.path import compile_path


class LogicNatsHandler(AsyncHandler[Msg]):
    subscription: Optional[Union[Subscription, JetStreamContext.PushSubscription]]

    def __init__(
        self,
        subject: str,
        log_context_builder: Callable[[StreamMessage[Any]], Dict[str, str]],
        queue: str = "",
        stream: Optional[JStream] = None,
        extra_options: Optional[AnyDict] = None,
        # AsyncAPI information
        description: Optional[str] = None,
        title: Optional[str] = None,
    ):
        reg, path = compile_path(subject, replace_symbol="*")
        self.subject = path
        self.path_regex = reg

        self.queue = queue

        self.stream = stream
        self.extra_options = extra_options or {}

        super().__init__(
            log_context_builder=log_context_builder,
            description=description,
            title=title,
        )

        self.subscription = None

    def add_call(
        self,
        *,
        handler: HandlerCallWrapper[Msg, P_HandlerParams, T_HandlerReturn],
        dependant: CallModel[P_HandlerParams, T_HandlerReturn],
        parser: Optional[CustomParser[Msg, NatsMessage]],
        decoder: Optional[CustomDecoder[NatsMessage]],
        filter: Filter[NatsMessage],
        middlewares: Optional[Sequence[Callable[[Msg], BaseMiddleware]]],
    ) -> None:
        parser_ = Parser if self.stream is None else JsParser
        super().add_call(
            handler=handler,
            parser=resolve_custom_func(parser, parser_.parse_message),
            decoder=resolve_custom_func(decoder, parser_.decode_message),
            filter=filter,  # type: ignore[arg-type]
            dependant=dependant,
            middlewares=middlewares,
        )

    @override
    async def start(self, connection: Union[Client, JetStreamContext]) -> None:  # type: ignore[override]
        self.subscription = await connection.subscribe(
            subject=self.subject,
            queue=self.queue,
            cb=self.consume,  # type: ignore[arg-type]
            **self.extra_options,
        )

    async def close(self) -> None:
        if self.subscription is not None:
            await self.subscription.unsubscribe()
            self.subscription = None

    @staticmethod
    def get_routing_hash(subject: str) -> str:
        return subject
