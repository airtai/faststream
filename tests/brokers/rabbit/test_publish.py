import asyncio
from unittest.mock import Mock, patch

import pytest

from faststream.rabbit import RabbitBroker, ReplyConfig
from faststream.rabbit.publisher.producer import AioPikaFastProducer
from tests.brokers.base.publish import BrokerPublishTestcase
from tests.tools import spy_decorator


@pytest.mark.rabbit()
class TestPublish(BrokerPublishTestcase):
    def get_broker(self, apply_types: bool = False) -> RabbitBroker:
        return RabbitBroker(apply_types=apply_types)

    @pytest.mark.asyncio()
    async def test_reply_config(
        self,
        queue: str,
        event: asyncio.Event,
        mock: Mock,
    ):
        pub_broker = self.get_broker()

        reply_queue = queue + "reply"

        @pub_broker.subscriber(reply_queue)
        async def reply_handler(m):
            event.set()
            mock(m)

        with pytest.warns(DeprecationWarning):

            @pub_broker.subscriber(queue, reply_config=ReplyConfig(persist=True))
            async def handler(m):
                return m

        async with self.patch_broker(pub_broker) as br:
            with patch.object(
                AioPikaFastProducer,
                "publish",
                spy_decorator(AioPikaFastProducer.publish),
            ) as m:
                await br.start()

                await asyncio.wait(
                    (
                        asyncio.create_task(
                            br.publish("Hello!", queue, reply_to=reply_queue)
                        ),
                        asyncio.create_task(event.wait()),
                    ),
                    timeout=3,
                )

                assert m.mock.call_args.kwargs.get("persist")
                assert m.mock.call_args.kwargs.get("immediate") is False

        assert event.is_set()
        mock.assert_called_with("Hello!")
