import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Tuple
from unittest.mock import Mock

import anyio
import pytest
from pydantic import BaseModel

from faststream._compat import dump_json, model_to_json
from faststream.annotations import Logger
from faststream.broker.core.usecase import BrokerUsecase


class SimpleModel(BaseModel):
    r: str


@dataclass
class SimpleDataclass:
    r: str


now = datetime.now()


class BrokerPublishTestcase:
    timeout: int = 3
    subscriber_kwargs: ClassVar[Dict[str, Any]] = {}

    @pytest.fixture()
    def pub_broker(self, full_broker):
        return full_broker

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        ("message", "message_type", "expected_message"),
        (  # noqa: PT007
            pytest.param(
                "hello",
                str,
                "hello",
                id="str->str",
            ),
            pytest.param(
                b"hello",
                bytes,
                b"hello",
                id="bytes->bytes",
            ),
            pytest.param(
                1,
                int,
                1,
                id="int->int",
            ),
            pytest.param(
                1.0,
                float,
                1.0,
                id="float->float",
            ),
            pytest.param(
                1,
                float,
                1.0,
                id="int->float",
            ),
            pytest.param(
                False,
                bool,
                False,
                id="bool->bool",
            ),
            pytest.param(
                {"m": 1},
                Dict[str, int],
                {"m": 1},
                id="dict->dict",
            ),
            pytest.param(
                [1, 2, 3],
                List[int],
                [1, 2, 3],
                id="list->list",
            ),
            pytest.param(
                now,
                datetime,
                now,
                id="datetime->datetime",
            ),
            pytest.param(
                model_to_json(SimpleModel(r="hello!")).encode(),
                SimpleModel,
                SimpleModel(r="hello!"),
                id="bytes->model",
            ),
            pytest.param(
                SimpleModel(r="hello!"),
                SimpleModel,
                SimpleModel(r="hello!"),
                id="model->model",
            ),
            pytest.param(
                SimpleModel(r="hello!"),
                dict,
                {"r": "hello!"},
                id="model->dict",
            ),
            pytest.param(
                {"r": "hello!"},
                SimpleModel,
                SimpleModel(r="hello!"),
                id="dict->model",
            ),
            pytest.param(
                dump_json(asdict(SimpleDataclass(r="hello!"))),
                SimpleDataclass,
                SimpleDataclass(r="hello!"),
                id="bytes->dataclass",
            ),
            pytest.param(
                SimpleDataclass(r="hello!"),
                SimpleDataclass,
                SimpleDataclass(r="hello!"),
                id="dataclass->dataclass",
            ),
            pytest.param(
                SimpleDataclass(r="hello!"),
                dict,
                {"r": "hello!"},
                id="dataclass->dict",
            ),
            pytest.param(
                {"r": "hello!"},
                SimpleDataclass,
                SimpleDataclass(r="hello!"),
                id="dict->dataclass",
            ),
        ),
    )
    async def test_serialize(
        self,
        pub_broker: BrokerUsecase,
        mock: Mock,
        queue: str,
        message,
        message_type,
        expected_message,
        event,
    ):
        @pub_broker.subscriber(queue, **self.subscriber_kwargs)
        async def handler(m: message_type, logger: Logger):
            event.set()
            mock(m)

        async with pub_broker:
            await pub_broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(pub_broker.publish(message, queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_with(expected_message)

    @pytest.mark.asyncio()
    async def test_unwrap_dict(
        self, mock: Mock, queue: str, pub_broker: BrokerUsecase, event
    ):
        @pub_broker.subscriber(queue, **self.subscriber_kwargs)
        async def m(a: int, b: int, logger: Logger):
            event.set()
            mock({"a": a, "b": b})

        async with pub_broker:
            await pub_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(pub_broker.publish({"a": 1, "b": 1.0}, queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_with(
            {
                "a": 1,
                "b": 1,
            }
        )

    @pytest.mark.asyncio()
    async def test_unwrap_list(
        self, mock: Mock, queue: str, pub_broker: BrokerUsecase, event: asyncio.Event
    ):
        @pub_broker.subscriber(queue, **self.subscriber_kwargs)
        async def m(a: int, b: int, *args: Tuple[int, ...], logger: Logger):
            event.set()
            mock({"a": a, "b": b, "args": args})

        async with pub_broker:
            await pub_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(pub_broker.publish([1, 1.0, 2.0, 3.0], queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_with({"a": 1, "b": 1, "args": (2, 3)})

    @pytest.mark.asyncio()
    async def test_base_publisher(
        self,
        queue: str,
        pub_broker: BrokerUsecase,
        event,
        mock,
    ):
        @pub_broker.subscriber(queue, **self.subscriber_kwargs)
        @pub_broker.publisher(queue + "resp")
        async def m():
            return ""

        @pub_broker.subscriber(queue + "resp", **self.subscriber_kwargs)
        async def resp(msg):
            event.set()
            mock(msg)

        async with pub_broker:
            await pub_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(pub_broker.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_once_with("")

    @pytest.mark.asyncio()
    async def test_publisher_object(
        self,
        queue: str,
        pub_broker: BrokerUsecase,
        event,
        mock,
    ):
        publisher = pub_broker.publisher(queue + "resp")

        @publisher
        @pub_broker.subscriber(queue, **self.subscriber_kwargs)
        async def m():
            return ""

        @pub_broker.subscriber(queue + "resp", **self.subscriber_kwargs)
        async def resp(msg):
            event.set()
            mock(msg)

        async with pub_broker:
            await pub_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(pub_broker.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_once_with("")

    @pytest.mark.asyncio()
    async def test_publish_manual(
        self,
        queue: str,
        pub_broker: BrokerUsecase,
        event,
        mock,
    ):
        publisher = pub_broker.publisher(queue + "resp")

        @pub_broker.subscriber(queue, **self.subscriber_kwargs)
        async def m():
            await publisher.publish("")

        @pub_broker.subscriber(queue + "resp", **self.subscriber_kwargs)
        async def resp(msg):
            event.set()
            mock(msg)

        async with pub_broker:
            await pub_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(pub_broker.publish("", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_once_with("")

    @pytest.mark.asyncio()
    async def test_multiple_publishers(
        self, queue: str, pub_broker: BrokerUsecase, mock
    ):
        event = anyio.Event()
        event2 = anyio.Event()

        @pub_broker.publisher(queue + "resp2")
        @pub_broker.subscriber(queue, **self.subscriber_kwargs)
        @pub_broker.publisher(queue + "resp")
        async def m():
            return ""

        @pub_broker.subscriber(queue + "resp", **self.subscriber_kwargs)
        async def resp(msg):
            event.set()
            mock.resp1(msg)

        @pub_broker.subscriber(queue + "resp2", **self.subscriber_kwargs)
        async def resp2(msg):
            event2.set()
            mock.resp2(msg)

        async with pub_broker:
            await pub_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(pub_broker.publish("", queue)),
                    asyncio.create_task(event.wait()),
                    asyncio.create_task(event2.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        assert event2.is_set()
        mock.resp1.assert_called_once_with("")
        mock.resp2.assert_called_once_with("")

    @pytest.mark.asyncio()
    async def test_reusable_publishers(
        self, queue: str, pub_broker: BrokerUsecase, mock
    ):
        consume = anyio.Event()
        consume2 = anyio.Event()

        pub = pub_broker.publisher(queue + "resp")

        @pub
        @pub_broker.subscriber(queue, **self.subscriber_kwargs)
        async def m():
            return ""

        @pub
        @pub_broker.subscriber(queue + "2", **self.subscriber_kwargs)
        async def m2():
            return ""

        @pub_broker.subscriber(queue + "resp", **self.subscriber_kwargs)
        async def resp():
            if not consume.is_set():
                consume.set()
            else:
                consume2.set()
            mock()

        async with pub_broker:
            await pub_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(pub_broker.publish("", queue)),
                    asyncio.create_task(pub_broker.publish("", queue + "2")),
                    asyncio.create_task(consume.wait()),
                    asyncio.create_task(consume2.wait()),
                ),
                timeout=self.timeout,
            )

        assert consume2.is_set()
        assert consume.is_set()
        assert mock.call_count == 2

    @pytest.mark.asyncio()
    async def test_reply_to(
        self,
        pub_broker: BrokerUsecase,
        queue: str,
        event,
        mock,
    ):
        @pub_broker.subscriber(queue + "reply", **self.subscriber_kwargs)
        async def reply_handler(m):
            event.set()
            mock(m)

        @pub_broker.subscriber(queue, **self.subscriber_kwargs)
        async def handler(m):
            return m

        async with pub_broker:
            await pub_broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(
                        pub_broker.publish("Hello!", queue, reply_to=queue + "reply")
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_with("Hello!")

    @pytest.mark.asyncio()
    async def test_publisher_after_start(
        self,
        pub_broker: BrokerUsecase,
        queue: str,
        event,
        mock,
    ):
        @pub_broker.subscriber(queue, **self.subscriber_kwargs)
        async def handler(m):
            event.set()
            mock(m)

        async with pub_broker:
            await pub_broker.start()

            pub = pub_broker.publisher(queue)

            await asyncio.wait(
                (
                    asyncio.create_task(pub.publish("Hello!")),
                    asyncio.create_task(event.wait()),
                ),
                timeout=self.timeout,
            )

        assert event.is_set()
        mock.assert_called_with("Hello!")
