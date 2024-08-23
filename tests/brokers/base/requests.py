import anyio
import pytest

from faststream import BaseMiddleware

from .basic import BaseTestcaseConfig


class Mid(BaseMiddleware):
    async def consume_scope(self, call_next, msg):
        msg._decoded_body = msg._decoded_body * 2
        return await call_next(msg)


class RequestsTestcase(BaseTestcaseConfig):
    def get_broker(self, **kwargs):
        raise NotImplementedError

    def get_router(self, **kwargs):
        raise NotImplementedError

    def patch_broker(self, broker, **kwargs):
        return broker

    async def test_request_timeout(self, queue: str):
        broker = self.get_broker()

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler(msg):
            await anyio.sleep(1.0)
            return "Response"

        async with self.patch_broker(broker):
            await broker.start()

            with pytest.raises(TimeoutError):
                await broker.request(
                    None,
                    queue,
                    timeout=1e-24,
                )

    async def test_broker_base_request(self, queue: str):
        broker = self.get_broker()

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler(msg):
            return "Response"

        async with self.patch_broker(broker):
            await broker.start()

            response = await broker.request(
                None,
                queue,
                timeout=self.timeout,
                correlation_id="1",
            )

        assert await response.decode() == "Response"
        assert response.correlation_id == "1", response.correlation_id

    async def test_publisher_base_request(self, queue: str):
        broker = self.get_broker()

        publisher = broker.publisher(queue)

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler(msg):
            return "Response"

        async with self.patch_broker(broker):
            await broker.start()

            response = await publisher.request(
                None,
                timeout=self.timeout,
                correlation_id="1",
            )

        assert await response.decode() == "Response"
        assert response.correlation_id == "1", response.correlation_id

    async def test_router_publisher_request(self, queue: str):
        router = self.get_router()

        publisher = router.publisher(queue)

        args, kwargs = self.get_subscriber_params(queue)

        @router.subscriber(*args, **kwargs)
        async def handler(msg):
            return "Response"

        broker = self.get_broker()
        broker.include_router(router)

        async with self.patch_broker(broker):
            await broker.start()

            response = await publisher.request(
                None,
                timeout=self.timeout,
                correlation_id="1",
            )

        assert await response.decode() == "Response"
        assert response.correlation_id == "1", response.correlation_id

    async def test_broker_request_respect_middleware(self, queue: str):
        broker = self.get_broker(middlewares=(Mid,))

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler(msg):
            return msg

        async with self.patch_broker(broker):
            await broker.start()

            response = await broker.request(
                "x",
                queue,
                timeout=self.timeout,
            )

        assert await response.decode() == "x" * 2 * 2

    async def test_broker_publisher_request_respect_middleware(self, queue: str):
        broker = self.get_broker(middlewares=(Mid,))

        publisher = broker.publisher(queue)

        args, kwargs = self.get_subscriber_params(queue)

        @broker.subscriber(*args, **kwargs)
        async def handler(msg):
            return msg

        async with self.patch_broker(broker):
            await broker.start()

            response = await publisher.request(
                "x",
                timeout=self.timeout,
            )

        assert await response.decode() == "x" * 2 * 2

    async def test_router_publisher_request_respect_middleware(self, queue: str):
        router = self.get_router(middlewares=(Mid,))

        publisher = router.publisher(queue)

        args, kwargs = self.get_subscriber_params(queue)

        @router.subscriber(*args, **kwargs)
        async def handler(msg):
            return msg

        broker = self.get_broker()
        broker.include_router(router)

        async with self.patch_broker(broker):
            await broker.start()

            response = await publisher.request(
                "x",
                timeout=self.timeout,
            )

        assert await response.decode() == "x" * 2 * 2
