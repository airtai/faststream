import asyncio
from abc import abstractmethod
from unittest.mock import Mock

import anyio
import pytest

from .consume import BrokerConsumeTestcase
from .publish import BrokerPublishTestcase


class BrokerTestclientTestcase(BrokerPublishTestcase, BrokerConsumeTestcase):
    @abstractmethod
    def get_fake_producer_class(self) -> type:
        raise NotImplementedError

    @pytest.mark.asyncio()
    async def test_correct_clean_fake_subscribers(self) -> None:
        broker = self.get_broker()

        @broker.subscriber("test")
        async def handler1(msg) -> None: ...

        broker.publisher("test2")
        broker.publisher("test")

        assert len(broker._subscribers) == 1

        test_client = self.patch_broker(broker)
        async with test_client as br:
            assert len(br._subscribers) == 2

        assert len(broker._subscribers) == 1

    @pytest.mark.asyncio()
    async def test_subscriber_mock(self, queue: str) -> None:
        test_broker = self.get_broker()

        args, kwargs = self.get_subscriber_params(queue)

        @test_broker.subscriber(*args, **kwargs)
        async def m(msg) -> None:
            pass

        async with self.patch_broker(test_broker) as br:
            await br.start()
            await br.publish("hello", queue)
            m.mock.assert_called_once_with("hello")

    @pytest.mark.asyncio()
    async def test_publisher_mock(self, queue: str) -> None:
        test_broker = self.get_broker()

        publisher = test_broker.publisher(queue + "resp")

        args, kwargs = self.get_subscriber_params(queue)

        @publisher
        @test_broker.subscriber(*args, **kwargs)
        async def m(msg) -> str:
            return "response"

        async with self.patch_broker(test_broker) as br:
            await br.start()
            await br.publish("hello", queue)
            publisher.mock.assert_called_with("response")

    @pytest.mark.asyncio()
    async def test_publisher_with_subscriber__mock(self, queue: str) -> None:
        test_broker = self.get_broker()

        publisher = test_broker.publisher(queue + "resp")

        args, kwargs = self.get_subscriber_params(queue)

        @publisher
        @test_broker.subscriber(*args, **kwargs)
        async def m(msg) -> str:
            return "response"

        args2, kwargs2 = self.get_subscriber_params(queue + "resp")

        @test_broker.subscriber(*args2, **kwargs2)
        async def handler_response(msg) -> None: ...

        async with self.patch_broker(test_broker) as br:
            await br.start()

            assert len(br._subscribers) == 2

            await br.publish("hello", queue)
            publisher.mock.assert_called_with("response")
            handler_response.mock.assert_called_once_with("response")

    @pytest.mark.asyncio()
    async def test_manual_publisher_mock(self, queue: str) -> None:
        test_broker = self.get_broker()

        publisher = test_broker.publisher(queue + "resp")

        args, kwargs = self.get_subscriber_params(queue)

        @test_broker.subscriber(*args, **kwargs)
        async def m(msg) -> None:
            await publisher.publish("response")

        async with self.patch_broker(test_broker) as br:
            await br.start()
            await br.publish("hello", queue)
            publisher.mock.assert_called_with("response")

    @pytest.mark.asyncio()
    async def test_exception_raises(self, queue: str) -> None:
        test_broker = self.get_broker()

        args, kwargs = self.get_subscriber_params(queue)

        @test_broker.subscriber(*args, **kwargs)
        async def m(msg):  # pragma: no cover
            raise ValueError

        async with self.patch_broker(test_broker) as br:
            await br.start()

            with pytest.raises(ValueError):  # noqa: PT011
                await br.publish("hello", queue)

    @pytest.mark.asyncio()
    async def test_parser_exception_raises(self, queue: str) -> None:
        test_broker = self.get_broker()

        def parser(msg):
            raise ValueError

        args, kwargs = self.get_subscriber_params(queue, parser=parser)

        @test_broker.subscriber(*args, **kwargs)
        async def m(msg):  # pragma: no cover
            pass

        async with self.patch_broker(test_broker) as br:
            await br.start()

            with pytest.raises(ValueError):  # noqa: PT011
                await br.publish("hello", queue)

    async def test_broker_gets_patched_attrs_within_cm(self, fake_producer_cls) -> None:
        test_broker = self.get_broker()
        await test_broker.start()

        old_producer = test_broker._producer

        async with self.patch_broker(test_broker) as br:
            assert isinstance(br.start, Mock)
            assert isinstance(br._connect, Mock)
            assert isinstance(br.close, Mock)
            assert isinstance(br._producer, fake_producer_cls)

        assert not isinstance(br.start, Mock)
        assert not isinstance(br._connect, Mock)
        assert not isinstance(br.close, Mock)
        assert br._connection is not None
        assert br._producer == old_producer

    async def test_broker_with_real_doesnt_get_patched(self) -> None:
        test_broker = self.get_broker()
        await test_broker.start()

        async with self.patch_broker(test_broker, with_real=True) as br:
            assert not isinstance(br.start, Mock)
            assert not isinstance(br._connect, Mock)
            assert not isinstance(br.close, Mock)
            assert br._connection is not None
            assert br._producer is not None

    async def test_broker_with_real_patches_publishers_and_subscribers(
        self,
        queue: str,
    ) -> None:
        test_broker = self.get_broker()

        publisher = test_broker.publisher(f"{queue}1")

        args, kwargs = self.get_subscriber_params(queue)

        @test_broker.subscriber(*args, **kwargs)
        async def m(msg) -> None:
            await publisher.publish(f"response: {msg}")

        async with self.patch_broker(test_broker, with_real=True) as br:
            await br.publish("hello", queue)
            await m.wait_call(self.timeout)
            m.mock.assert_called_once_with("hello")

            with anyio.fail_after(self.timeout):
                while not publisher.mock.called:  # noqa: ASYNC110
                    await asyncio.sleep(0.1)

                publisher.mock.assert_called_once_with("response: hello")
