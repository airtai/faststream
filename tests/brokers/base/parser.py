import asyncio
from typing import Type
from unittest.mock import Mock

import pytest

from faststream._internal.broker.broker import BrokerUsecase

from .basic import BaseTestcaseConfig


@pytest.mark.asyncio
class LocalCustomParserTestcase(BaseTestcaseConfig):
    broker_class: Type[BrokerUsecase]

    @pytest.fixture
    def raw_broker(self):
        return None

    def patch_broker(
        self, raw_broker: BrokerUsecase, broker: BrokerUsecase
    ) -> BrokerUsecase:
        return broker

    async def test_local_parser(
        self,
        mock: Mock,
        queue: str,
        raw_broker,
        event: asyncio.Event,
    ):
        broker = self.broker_class()

        async def custom_parser(msg, original):
            msg = await original(msg)
            mock(msg.body)
            return msg

        args, kwargs = self.get_subscriber_params(queue, parser=custom_parser)

        @broker.subscriber(*args, **kwargs)
        async def handle(m):
            event.set()

        broker = self.patch_broker(raw_broker, broker)
        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish(b"hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

            assert event.is_set()
            mock.assert_called_once_with(b"hello")

    async def test_local_sync_decoder(
        self,
        mock: Mock,
        queue: str,
        raw_broker,
        event: asyncio.Event,
    ):
        broker = self.broker_class()

        def custom_decoder(msg):
            mock(msg.body)
            return msg

        args, kwargs = self.get_subscriber_params(queue, decoder=custom_decoder)

        @broker.subscriber(*args, **kwargs)
        async def handle(m):
            event.set()

        broker = self.patch_broker(raw_broker, broker)
        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish(b"hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

            assert event.is_set()
            mock.assert_called_once_with(b"hello")

    async def test_global_sync_decoder(
        self,
        mock: Mock,
        queue: str,
        raw_broker,
        event: asyncio.Event,
    ):
        def custom_decoder(msg):
            mock(msg.body)
            return msg

        broker = self.broker_class(decoder=custom_decoder)

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handle(m):
            event.set()

        broker = self.patch_broker(raw_broker, broker)
        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish(b"hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

            assert event.is_set()
            mock.assert_called_once_with(b"hello")

    async def test_local_parser_no_share_between_subscribers(
        self,
        event: asyncio.Event,
        mock: Mock,
        queue: str,
        raw_broker,
    ):
        event2 = asyncio.Event()
        broker = self.broker_class()

        async def custom_parser(msg, original):
            msg = await original(msg)
            mock(msg.body)
            return msg

        args, kwargs = self.get_subscriber_params(queue, parser=custom_parser)
        args2, kwargs2 = self.get_subscriber_params(queue + "1")

        @broker.subscriber(*args, **kwargs)
        @broker.subscriber(*args2, **kwargs2)
        async def handle(m):
            if event.is_set():
                event2.set()
            else:
                event.set()

        broker = self.patch_broker(raw_broker, broker)
        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish(b"hello", queue)),
                    asyncio.create_task(broker.publish(b"hello", queue + "1")),
                    asyncio.create_task(event.wait()),
                    asyncio.create_task(event2.wait()),
                ),
                timeout=self.timeout,
            )

            assert event.is_set()
            assert event2.is_set()
            mock.assert_called_once_with(b"hello")

    async def test_local_parser_no_share_between_handlers(
        self,
        mock: Mock,
        queue: str,
        raw_broker,
        event: asyncio.Event,
    ):
        broker = self.broker_class()

        args, kwargs = self.get_subscriber_params(queue)
        sub = broker.subscriber(*args, **kwargs)

        @sub(filter=lambda m: m.content_type == "application/json")
        async def handle(m):
            event.set()

        event2 = asyncio.Event()

        async def custom_parser(msg, original):
            msg = await original(msg)
            mock(msg.body)
            return msg

        @sub(parser=custom_parser)
        async def handle2(m):
            event2.set()

        broker = self.patch_broker(raw_broker, broker)
        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish({"msg": "hello"}, queue)),
                    asyncio.create_task(broker.publish(b"hello", queue)),
                    asyncio.create_task(event.wait()),
                    asyncio.create_task(event2.wait()),
                ),
                timeout=self.timeout,
            )

            assert event.is_set()
            assert event2.is_set()
            assert mock.call_count == 1


class CustomParserTestcase(LocalCustomParserTestcase):
    async def test_global_parser(
        self,
        mock: Mock,
        queue: str,
        raw_broker,
        event: asyncio.Event,
    ):
        async def custom_parser(msg, original):
            msg = await original(msg)
            mock(msg.body)
            return msg

        broker = self.broker_class(parser=custom_parser)

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handle(m):
            event.set()

        broker = self.patch_broker(raw_broker, broker)
        async with broker:
            await broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(broker.publish(b"hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

            assert event.is_set()
            mock.assert_called_once_with(b"hello")
