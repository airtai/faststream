from typing import Any, ClassVar, Mapping

import anyio
import pytest


class RequestsTestcase:
    timeout: float = 3.0
    subscriber_kwargs: ClassVar[Mapping[str, Any]] = {}

    def get_broker(self):
        raise NotImplementedError

    def get_router(self):
        raise NotImplementedError

    def patch_broker(self, broker):
        return broker

    async def test_request_timeout(self, queue: str):
        broker = self.get_broker()

        @broker.subscriber(queue, **self.subscriber_kwargs)
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

        @broker.subscriber(queue, **self.subscriber_kwargs)
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

        assert response.decoded_body == "Response"
        assert response.correlation_id == "1", response.correlation_id

    async def test_publisher_base_request(self, queue: str):
        broker = self.get_broker()

        publisher = broker.publisher(queue)

        @broker.subscriber(queue, **self.subscriber_kwargs)
        async def handler(msg):
            return "Response"

        async with self.patch_broker(broker):
            await broker.start()

            response = await publisher.request(
                None,
                timeout=self.timeout,
                correlation_id="1",
            )

        assert response.decoded_body == "Response"
        assert response.correlation_id == "1", response.correlation_id

    async def test_router_publisher_request(self, queue: str):
        router = self.get_router()

        publisher = router.publisher(queue)

        @router.subscriber(queue, **self.subscriber_kwargs)
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

        assert response.decoded_body == "Response"
        assert response.correlation_id == "1", response.correlation_id
