from faststream.asyncapi.generate import get_app_schema
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue
from tests.asyncapi.base.v3_0_0.arguments import ArgumentsTestcase


class TestArguments(ArgumentsTestcase):
    broker_class = RabbitBroker

    def test_subscriber_bindings(self):
        broker = self.broker_class()

        @broker.subscriber(
            RabbitQueue("test", auto_delete=True),
            RabbitExchange("test-ex", type=ExchangeType.TOPIC),
        )
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "amqp": {
                "bindingVersion": "0.2.0",
                "exchange": {
                    "autoDelete": False,
                    "durable": False,
                    "name": "test-ex",
                    "type": "topic",
                    "vhost": "/",
                },
                "is": "routingKey",
                "queue": {
                    "autoDelete": True,
                    "durable": False,
                    "exclusive": False,
                    "name": "test",
                    "vhost": "/",
                },
            }
        }

    def test_subscriber_fanout_bindings(self):
        broker = self.broker_class()

        @broker.subscriber(
            RabbitQueue("test", auto_delete=True),
            RabbitExchange("test-ex", type=ExchangeType.FANOUT),
        )
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "amqp": {
                "bindingVersion": "0.2.0",
                "exchange": {
                    "autoDelete": False,
                    "durable": False,
                    "name": "test-ex",
                    "type": "fanout",
                    "vhost": "/",
                },
                "is": "routingKey",
            }
        }
