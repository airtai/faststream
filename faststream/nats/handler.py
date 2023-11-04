import asyncio

from typing import Any, Callable, Dict, Optional, Sequence, Union

from fast_depends.core import CallModel
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.js import JetStreamContext
from nats.js.kv import KeyValue
from nats.js.object_store import ObjectStore

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
from faststream.nats.pull_sub import PullSub
from faststream.nats.kv_watch import KvWatch
from faststream.nats.obj_watch import ObjWatch
from faststream.nats.message import NatsMessage
from faststream.nats.parser import JsParser, Parser
from faststream.types import AnyDict
from faststream.utils.context.path import compile_path


class LogicNatsHandler(AsyncHandler[Msg]):
    subscription: Optional[Union[Subscription, JetStreamContext.PushSubscription, JetStreamContext.PullSubscription]]
    task: Optional["asyncio.Task[Any]"] = None

    def __init__(
        self,
        subject: str,
        log_context_builder: Callable[[StreamMessage[Any]], Dict[str, str]],
        queue: str = "",
        stream: Optional[JStream] = None,
        pull_sub: Optional[PullSub] = None,
        kv_watch: Optional[KvWatch] = None,
        obj_watch: Optional[ObjWatch] = None,
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
        self.pull_sub = pull_sub
        self.kv_watch = kv_watch
        self.obj_watch = obj_watch
        self.extra_options = extra_options or {}

        super().__init__(
            log_context_builder=log_context_builder,
            description=description,
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
            self.subscription = await connection.pull_subscribe(
                subject=self.subject,
                **self.extra_options
            )
            self.task = asyncio.create_task(self._consume())

        elif self.kv_watch is not None:
            bucket = await connection.key_value(self.kv_watch.bucket)
            watcher = await bucket.watch(self.kv_watch.keys, **self.extra_options)
            self.task = asyncio.create_task(self._cosume_watch(watcher))

        elif self.obj_watch is not None:
            bucket = await connection.object_store(self.obj_watch.bucket)
            watcher = await bucket.watch(**self.extra_options)
            self.task = asyncio.create_task(self._cosume_watch(watcher))

        else:
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

        if self.task is not None:
            self.task.cancel()
            self.task = None

    async def _consume(self) -> None:
        while self.subscription:
            messages = await self.subscription.fetch(self.pull_sub.batch_size)
            await asyncio.gather(*[self.consume(message)] for message in messages)

    async def _cosume_watch(self, watcher: Union[KeyValue.KeyWatcher, ObjectStore.ObjectWatcher]) -> None:
        while self.subscription:
            message = await watcher.updates()
            await self.consume(message)

    @staticmethod
    def get_routing_hash(subject: str) -> str:
        return subject
