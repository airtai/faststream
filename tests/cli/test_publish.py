from unittest.mock import AsyncMock, patch

from dirty_equals import IsPartialDict

from faststream import FastStream
from faststream._internal.cli.main import cli as faststream_app
from tests.marks import (
    require_aiokafka,
    require_aiopika,
    require_confluent,
    require_nats,
    require_redis,
)


def get_mock_app(broker_type, producer_type) -> FastStream:
    broker = broker_type()
    broker.connect = AsyncMock()
    mock_producer = AsyncMock(spec=producer_type)
    mock_producer.publish = AsyncMock()
    broker._producer = mock_producer
    return FastStream(broker)


@require_redis
def test_publish_command_with_redis_options(runner):
    from faststream.redis import RedisBroker
    from faststream.redis.publisher.producer import RedisFastProducer

    mock_app = get_mock_app(RedisBroker, RedisFastProducer)

    with patch(
        "faststream._internal.cli.main.import_from_string",
        return_value=(None, mock_app),
    ):
        result = runner.invoke(
            faststream_app,
            [
                "publish",
                "fastream:app",
                "hello world",
                "--channel",
                "test channel",
                "--reply_to",
                "tester",
                "--list",
                "0.1",
                "--stream",
                "stream url",
                "--correlation_id",
                "someId",
            ],
        )

        assert result.exit_code == 0

        assert mock_app.broker._producer.publish.call_args.args[0] == "hello world"
        assert mock_app.broker._producer.publish.call_args.kwargs == IsPartialDict(
            channel="test channel",
            reply_to="tester",
            list="0.1",
            stream="stream url",
            correlation_id="someId",
            rpc=False,
        )


@require_confluent
def test_publish_command_with_confluent_options(runner):
    from faststream.confluent import KafkaBroker as ConfluentBroker
    from faststream.confluent.publisher.producer import AsyncConfluentFastProducer

    mock_app = get_mock_app(ConfluentBroker, AsyncConfluentFastProducer)

    with patch(
        "faststream._internal.cli.main.import_from_string",
        return_value=(None, mock_app),
    ):
        result = runner.invoke(
            faststream_app,
            [
                "publish",
                "fastream:app",
                "hello world",
                "--topic",
                "confluent topic",
                "--correlation_id",
                "someId",
            ],
        )

        assert result.exit_code == 0
        assert mock_app.broker._producer.publish.call_args.args[0] == "hello world"
        assert mock_app.broker._producer.publish.call_args.kwargs == IsPartialDict(
            topic="confluent topic",
            correlation_id="someId",
            rpc=False,
        )


@require_aiokafka
def test_publish_command_with_kafka_options(runner):
    from faststream.kafka import KafkaBroker
    from faststream.kafka.publisher.producer import AioKafkaFastProducer

    mock_app = get_mock_app(KafkaBroker, AioKafkaFastProducer)

    with patch(
        "faststream._internal.cli.main.import_from_string",
        return_value=(None, mock_app),
    ):
        result = runner.invoke(
            faststream_app,
            [
                "publish",
                "fastream:app",
                "hello world",
                "--topic",
                "kafka topic",
                "--correlation_id",
                "someId",
            ],
        )

        assert result.exit_code == 0
        assert mock_app.broker._producer.publish.call_args.args[0] == "hello world"
        assert mock_app.broker._producer.publish.call_args.kwargs == IsPartialDict(
            topic="kafka topic",
            correlation_id="someId",
            rpc=False,
        )


@require_nats
def test_publish_command_with_nats_options(runner):
    from faststream.nats import NatsBroker
    from faststream.nats.publisher.producer import NatsFastProducer

    mock_app = get_mock_app(NatsBroker, NatsFastProducer)

    with patch(
        "faststream._internal.cli.main.import_from_string",
        return_value=(None, mock_app),
    ):
        result = runner.invoke(
            faststream_app,
            [
                "publish",
                "fastream:app",
                "hello world",
                "--subject",
                "nats subject",
                "--reply_to",
                "tester",
                "--correlation_id",
                "someId",
            ],
        )

        assert result.exit_code == 0

        assert mock_app.broker._producer.publish.call_args.args[0] == "hello world"
        assert mock_app.broker._producer.publish.call_args.kwargs == IsPartialDict(
            subject="nats subject",
            reply_to="tester",
            correlation_id="someId",
            rpc=False,
        )


@require_aiopika
def test_publish_command_with_rabbit_options(runner):
    from faststream.rabbit import RabbitBroker
    from faststream.rabbit.publisher.producer import AioPikaFastProducer

    mock_app = get_mock_app(RabbitBroker, AioPikaFastProducer)

    with patch(
        "faststream._internal.cli.main.import_from_string",
        return_value=(None, mock_app),
    ):
        result = runner.invoke(
            faststream_app,
            [
                "publish",
                "fastream:app",
                "hello world",
                "--correlation_id",
                "someId",
                "--raise_timeout",
                "True",
            ],
        )

        assert result.exit_code == 0

        assert mock_app.broker._producer.publish.call_args.args[0] == "hello world"
        assert mock_app.broker._producer.publish.call_args.kwargs == IsPartialDict(
            {
                "correlation_id": "someId",
                "raise_timeout": "True",
                "rpc": False,
            }
        )
