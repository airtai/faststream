from faststream.asyncapi.generate import get_app_schema
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue
from tests.asyncapi.base.publisher import PublisherTestcase


class TestArguments(PublisherTestcase):
    broker_class = RabbitBroker

    def test_publisher_bindings(self):
        broker = self.broker_class()

        @broker.publisher(
            RabbitQueue("test", auto_delete=True),
            RabbitExchange("test-ex", type=ExchangeType.TOPIC),
        )
        async def handle(msg):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()
        key = tuple(schema["channels"].keys())[0]

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
