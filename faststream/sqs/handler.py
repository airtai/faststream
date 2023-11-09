import asyncio
import logging
from typing import Any, NoReturn, Optional

import anyio
from aiobotocore.client import AioBaseClient
from typing_extensions import TypeAlias

from faststream.broker.handler import AsyncHandler
from faststream.sqs.shared.schemas import SQSQueue
from faststream.types import AnyDict
from faststream.utils.context import context

QueueUrl: TypeAlias = str


class LogicSQSHandler(AsyncHandler[AnyDict]):
    queue: SQSQueue
    consumer_params: AnyDict
    task: Optional["asyncio.Task[Any]"] = None

    async def _consume(self, queue_url: str) -> NoReturn:
        c = self._get_log_context(None, self.queue.name)

        connected = True
        with context.scope("queue_url", queue_url):
            while True:
                try:
                    if connected is False:
                        await self.create_queue(self.queue)

                    r = await self._connection.receive_message(
                        QueueUrl=queue_url,
                        **self.consumer_params,
                    )

                except Exception as e:
                    if connected is True:
                        self._log(e, logging.WARNING, c, exc_info=e)
                        self._queues.pop(self.queue.name)
                        connected = False

                    await anyio.sleep(5)

                else:
                    if connected is False:
                        self._log("Connection established", logging.INFO, c)
                        connected = True

                    messages = r.get("Messages", [])
                    for msg in messages:
                        try:
                            await self.callback(msg, True)
                        except Exception:
                            has_trash_messages = True
                        else:
                            has_trash_messages = False

                    if has_trash_messages is True:
                        await anyio.sleep(
                            self.consumer_params.get("WaitTimeSeconds", 1.0)
                        )

    async def start(self, client: AioBaseClient) -> None:
        url = await self.create_queue(self.queue)
        self.task = asyncio.create_task(self._consume(url))

    async def close(self) -> None:
        pass
