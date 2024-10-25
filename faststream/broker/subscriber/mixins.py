import asyncio
from typing import (
    TYPE_CHECKING,
    Any,
    Coroutine,
    List,
)

import anyio

from .usecase import SubscriberUsecase

if TYPE_CHECKING:
    from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
    from nats.aio.msg import Msg


class TasksMixin(SubscriberUsecase[Any]):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.tasks: List[asyncio.Task[Any]] = []

    def add_task(self, coro: Coroutine[Any, Any, Any]) -> None:
        self.tasks.append(asyncio.create_task(coro))

    async def close(self) -> None:
        """Clean up handler subscription, cancel consume task in graceful mode."""
        await super().close()

        for task in self.tasks:
            if not task.done():
                task.cancel()

        self.tasks = []


class ConcurrentMixin(TasksMixin):
    send_stream: "MemoryObjectSendStream[Msg]"
    receive_stream: "MemoryObjectReceiveStream[Msg]"

    def __init__(
        self,
        *,
        max_workers: int,
        **kwargs: Any,
    ) -> None:
        self.max_workers = max_workers

        self.send_stream, self.receive_stream = anyio.create_memory_object_stream(
            max_buffer_size=max_workers
        )
        self.limiter = anyio.Semaphore(max_workers)

        super().__init__(**kwargs)

    def start_consume_task(self) -> None:
        self.add_task(self._serve_consume_queue())

    async def _serve_consume_queue(
        self,
    ) -> None:
        """Endless task consuming messages from in-memory queue.

        Suitable to batch messages by amount, timestamps, etc and call `consume` for this batches.
        """
        async with anyio.create_task_group() as tg:
            async for msg in self.receive_stream:
                tg.start_soon(self._consume_msg, msg)

    async def _consume_msg(
        self,
        msg: "Msg",
    ) -> None:
        """Proxy method to call `self.consume` with semaphore block."""
        async with self.limiter:
            await self.consume(msg)

    async def _put_msg(self, msg: "Msg") -> None:
        """Proxy method to put msg into in-memory queue with semaphore block."""
        async with self.limiter:
            await self.send_stream.send(msg)
