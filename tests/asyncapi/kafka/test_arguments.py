from aiokafka import TopicPartition

from faststream.asyncapi.generate import get_app_schema
from faststream.kafka import KafkaBroker
from tests.asyncapi.base.arguments import ArgumentsTestcase


class TestArguments(ArgumentsTestcase):
    broker_class = KafkaBroker

    def test_subscriber_bindings(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "kafka": {"bindingVersion": "0.4.0", "topic": "test"}
        }

    def test_subscriber_with_one_topic_partitions(self):
        broker = self.broker_class()

        part1 = TopicPartition("topic_name", 1)
        part2 = TopicPartition("topic_name", 2)

        @broker.subscriber(partitions=[part1, part2])
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "kafka": {"bindingVersion": "0.4.0", "topic": "topic_name"}
        }

    def test_subscriber_with_multi_topics_partitions(self):
        broker = self.broker_class()

        part1 = TopicPartition("topic_name1", 1)
        part2 = TopicPartition("topic_name2", 2)

        @broker.subscriber(partitions=[part1, part2])
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()
        key1 = tuple(schema["channels"].keys())[0]  # noqa: RUF015
        key2 = tuple(schema["channels"].keys())[1]

        assert sorted(
            (
                schema["channels"][key1]["bindings"]["kafka"]["topic"],
                schema["channels"][key2]["bindings"]["kafka"]["topic"],
            )
        ) == sorted(("topic_name1", "topic_name2"))
