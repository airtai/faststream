import asyncio
from contextlib import suppress
from typing import Any, Awaitable, Callable, Dict, Optional, Sequence, Union, cast

import anyio
from anyio.abc import TaskGroup, TaskStatus
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from fast_depends.core import CallModel
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.errors import TimeoutError
from nats.js import JetStreamContext
from typing_extensions import Annotated, Doc, override

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
from faststream.types import AnyDict, SendableMessage
from faststream.utils.path import compile_path


class LogicNatsHandler(AsyncHandler[Msg]):
    """A class to represent a NATS handler."""

    subscription: Union[
        None,
        Subscription,
        JetStreamContext.PushSubscription,
        JetStreamContext.PullSubscription,
    ]
    task_group: Optional[TaskGroup]
    task: Optional["asyncio.Task[Any]"]
    send_stream: MemoryObjectSendStream[Msg]
    receive_stream: MemoryObjectReceiveStream[Msg]

    def __init__(
        self,
        subject: Annotated[
            str,
            Doc("NATS subject to subscribe"),
        ],
        log_context_builder: Annotated[
            Callable[[StreamMessage[Any]], Dict[str, str]],
            Doc("Function to create log extra data by message"),
        ],
        queue: Annotated[
            str,
            Doc("NATS queue name"),
        ] = "",
        stream: Annotated[
            Optional[JStream],
            Doc("NATS Stream object"),
        ] = None,
        pull_sub: Annotated[
            Optional[PullSub],
            Doc("NATS Pull consumer parameters container"),
        ] = None,
        extra_options: Annotated[
            Optional[AnyDict],
            Doc("Extra arguments for subscription creation"),
        ] = None,
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Wait up to this time (if set) in graceful shutdown mode. "
                "Kills task forcefully if expired."
            ),
        ] = None,
        max_workers: Annotated[
            int,
            Doc("Process up to this parameter messages concurrently"),
        ] = 1,
        # AsyncAPI information
        description: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber description"),
        ] = None,
        title: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber title"),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whether to include the handler in AsyncAPI schema"),
        ] = True,
    ) -> None:
        """Initialize the NATS handler."""
        reg, path = compile_path(
            subject,
            replace_symbol="*",
            patch_regex=lambda x: x.replace(".>", "..+"),
        )
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
            graceful_timeout=graceful_timeout,
        )

        self.max_workers = max_workers
        self.subscription = None

        self.send_stream, self.receive_stream = anyio.create_memory_object_stream(
            max_buffer_size=max_workers
        )
        self.limiter = anyio.Semaphore(max_workers)
        self.task = None

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
    async def start(  # type: ignore[override]
        self,
        connection: Annotated[
            Union[Client, JetStreamContext],
            Doc("NATS client or JS Context object using to create subscription"),
        ],
    ) -> None:
        """Create NATS subscription and start consume task."""
        cb: Callable[[Msg], Awaitable[SendableMessage]]
        if self.max_workers > 1:
            self.task = asyncio.create_task(self._serve_consume_queue())
            cb = self.__put_msg
        else:
            cb = self.consume

        if self.pull_sub is not None:
            connection = cast(JetStreamContext, connection)

            if self.stream is None:
                raise ValueError("Pull subscriber can be used only with a stream")

            self.subscription = await connection.pull_subscribe(
                subject=self.subject,
                **self.extra_options,
            )
            self.task = asyncio.create_task(self._consume_pull(cb))

        else:
            self.subscription = await connection.subscribe(
                subject=self.subject,
                queue=self.queue,
                cb=cb,  # type: ignore[arg-type]
                **self.extra_options,
            )

        await super().start()

    async def close(self) -> None:
        """Clean up handler subscription, cancel consume task in graceful mode."""
        await super().close()

        if self.subscription is not None:
            await self.subscription.unsubscribe()
            self.subscription = None

        if self.task is not None:
            self.task.cancel()
            self.task = None

    async def _consume_pull(
        self,
        cb: Callable[[Msg], Awaitable[SendableMessage]],
        *,
        task_status: TaskStatus[None] = anyio.TASK_STATUS_IGNORED,
    ) -> None:
        """Endless task consuming messages using NATS Pull subscriber."""
        assert self.pull_sub  # nosec B101

        sub = cast(JetStreamContext.PullSubscription, self.subscription)

        task_status.started()

        while self.running:  # pragma: no branch
            with suppress(TimeoutError):
                messages = await sub.fetch(
                    batch=self.pull_sub.batch_size,
                    timeout=self.pull_sub.timeout,
                )

                if messages:
                    if self.pull_sub.batch:
                        await self.consume(messages)  # type: ignore[arg-type]

                    else:
                        async with anyio.create_task_group() as tg:
                            for msg in messages:
                                tg.start_soon(cb, msg)

    async def _serve_consume_queue(
        self,
        *,
        task_status: TaskStatus[None] = anyio.TASK_STATUS_IGNORED,
    ) -> None:
        """Endless task consuming messages from in-memory queue.

        Suitable to batch messages by amount, timestamps, etc and call `consume` for this batches.
        """
        async with anyio.create_task_group() as tg:
            task_status.started()

            async for msg in self.receive_stream:
                tg.start_soon(self.__consume_msg, msg)

    async def __consume_msg(
        self,
        msg: Msg,
    ) -> None:
        """Proxy method to call `self.consume` with semaphore block."""
        async with self.limiter:
            await self.consume(msg)

    async def __put_msg(self, msg: Msg) -> None:
        """Proxy method to put msg into in-memory queue with semaphore block."""
        async with self.limiter:
            await self.send_stream.send(msg)

    @staticmethod
    def get_routing_hash(
        subject: Annotated[str, Doc("NATS subject to consume messages")],
    ) -> str:
        """Get handler hash by outer data.

        Using to find handler in `broker.handlers` dictionary.
        """
        return subject
