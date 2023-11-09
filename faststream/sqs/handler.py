from aiobotocore.client import AioBaseClient

from faststream.broker.handler import AsyncHandler
from faststream.types import AnyDict


class LogicSQSHandler(AsyncHandler[AnyDict]):
    async def start(self, client: AioBaseClient) -> None:
        # TODO check "start" method on broker
        pass
