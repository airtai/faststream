from typing import Type

from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.broker.core.abc import BrokerUsecase


class NamingTestCase:
    broker_class: Type[BrokerUsecase]

    def test_naming(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle_user_created():
            ...

        schema = get_app_schema(FastStream(broker)).to_jsonable()

        assert tuple(schema["channels"].keys())[0] == "HandleUserCreatedTest"

    def test_multi_subscribers_naming(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        @broker.subscriber("test2")
        async def handle_user_created():
            ...

        schema = get_app_schema(FastStream(broker)).to_jsonable()

        assert set(schema["channels"].keys()) == {
            "HandleUserCreatedTest",
            "HandleUserCreatedTest2",
        }

    def test_naming_manual(self):
        broker = self.broker_class()

        @broker.subscriber("test", title="my_custom_name")
        async def handle_user_created():
            ...

        schema = get_app_schema(FastStream(broker)).to_jsonable()

        assert tuple(schema["channels"].keys())[0] == "my_custom_name"

    def test_multi_publishers_naming(self):
        broker = self.broker_class()

        @broker.publisher("test")
        @broker.publisher("test2")
        async def handle_user_created():
            ...

        schema = get_app_schema(FastStream(broker)).to_jsonable()

        assert set(schema["channels"].keys()) == {
            "TestPublisher",
            "Test2Publisher",
        }
