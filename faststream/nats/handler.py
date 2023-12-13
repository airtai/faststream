import asyncio
from contextlib import suppress
from typing import Any, Callable, Dict, Optional, Sequence, Union, cast

from fast_depends.core import CallModel
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.errors import TimeoutError
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
from faststream.nats.pull_sub import PullSub
from faststream.types import AnyDict
from faststream.utils.context.path import compile_path


class LogicNatsHandler(AsyncHandler[Msg]):
    subscription: Union[
        None,
        Subscription,
        JetStreamContext.PushSubscription,
        JetStreamContext.PullSubscription,
    ]
    task: Optional["asyncio.Task[Any]"] = None

    def __init__(
        self,
        subject: str,
        log_context_builder: Callable[[StreamMessage[Any]], Dict[str, str]],
        queue: str = "",
        stream: Optional[JStream] = None,
        pull_sub: Optional[PullSub] = None,
        extra_options: Optional[AnyDict] = None,
        # AsyncAPI information
        description: Optional[str] = None,
        title: Optional[str] = None,
        include_in_schema: bool = True,
    ):
        reg, path = compile_path(subject, replace_symbol="*")
        self.subject = path
        self.path_regex = reg

        self.queue = queue

        self.stream = stream
        self.pull_sub = pull_sub
        self.extra_options = extra_options or {}

        super().__init__(
            log_context_builder=log_context_builder,
            description=description,
            include_in_schema=include_in_schema,
            title=title,
        )

        self.task = None
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
        if self.pull_sub is not None:
            connection = cast(JetStreamContext, connection)

            if self.stream is None:
                raise ValueError("Pull subscriber can be used only with a stream")

            self.subscription = await connection.pull_subscribe(
                subject=self.subject,
                **self.extra_options,
            )
            self.task = asyncio.create_task(self._consume())

        else:
            self.subscription = await connection.subscribe(
                subject=self.subject,
                queue=self.queue,
                cb=self.consume,  # type: ignore[arg-type]
                **self.extra_options,
            )

        await super().start()

    async def close(self) -> None:
        await super().close()

        if self.subscription is not None:
            await self.subscription.unsubscribe()
            self.subscription = None

        if self.task is not None:
            self.task.cancel()
            self.task = None

    async def _consume(self) -> None:
        assert self.pull_sub  # nosec B101

        sub = cast(JetStreamContext.PullSubscription, self.subscription)

        while self.subscription is not None:  # pragma: no branch
            with suppress(TimeoutError):
                messages = await sub.fetch(
                    batch=self.pull_sub.batch_size,
                    timeout=self.pull_sub.timeout,
                )

                if messages:
                    if self.pull_sub.batch:
                        await self.consume(messages)  # type: ignore[arg-type]
                    else:
                        await asyncio.gather(*map(self.consume, messages))

    @staticmethod
    def get_routing_hash(subject: str) -> str:
        return subject
