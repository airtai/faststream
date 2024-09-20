from typing import Tuple
from unittest.mock import AsyncMock, patch

from dirty_equals import IsPartialDict
from typer.testing import CliRunner

from faststream import FastStream
from faststream._internal.cli.main import cli as faststream_app
from tests.marks import (
    require_aiokafka,
    require_aiopika,
    require_confluent,
    require_nats,
    require_redis,
)


def get_mock_app(broker_type, producer_type) -> Tuple[FastStream, AsyncMock]:
    broker = broker_type()
    broker.connect = AsyncMock()
    mock_producer = AsyncMock(spec=producer_type)
    mock_producer.publish = AsyncMock()
    mock_producer._parser = AsyncMock()
    mock_producer._decoder = AsyncMock()
    broker._producer = mock_producer
    return FastStream(broker), mock_producer


@require_redis
def test_publish_command_with_redis_options(runner):
    from faststream.redis import RedisBroker
    from faststream.redis.publisher.producer import RedisFastProducer

    mock_app, producer_mock = get_mock_app(RedisBroker, RedisFastProducer)

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
                "channelname",
                "--reply_to",
                "tester",
                "--list",
                "listname",
                "--stream",
                "streamname",
                "--correlation_id",
                "someId",
            ],
        )

        assert result.exit_code == 0

        assert producer_mock.publish.call_args.args[0] == "hello world"
        assert producer_mock.publish.call_args.kwargs == IsPartialDict(
            reply_to="tester",
            stream="streamname",
            list="listname",
            channel="channelname",
            correlation_id="someId",
        )


@require_confluent
def test_publish_command_with_confluent_options(runner):
    from faststream.confluent import KafkaBroker as ConfluentBroker
    from faststream.confluent.publisher.producer import AsyncConfluentFastProducer

    mock_app, producer_mock = get_mock_app(ConfluentBroker, AsyncConfluentFastProducer)

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
                "topicname",
                "--correlation_id",
                "someId",
            ],
        )

        assert result.exit_code == 0

        assert producer_mock.publish.call_args.args[0] == "hello world"
        assert producer_mock.publish.call_args.kwargs == IsPartialDict(
            topic="topicname",
            correlation_id="someId",
        )


@require_aiokafka
def test_publish_command_with_kafka_options(runner):
    from faststream.kafka import KafkaBroker
    from faststream.kafka.publisher.producer import AioKafkaFastProducer

    mock_app, producer_mock = get_mock_app(KafkaBroker, AioKafkaFastProducer)

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
                "topicname",
                "--correlation_id",
                "someId",
            ],
        )

        assert result.exit_code == 0
        assert producer_mock.publish.call_args.args[0] == "hello world"
        assert producer_mock.publish.call_args.kwargs == IsPartialDict(
            topic="topicname",
            correlation_id="someId",
        )


@require_nats
def test_publish_command_with_nats_options(runner):
    from faststream.nats import NatsBroker
    from faststream.nats.publisher.producer import NatsFastProducer

    mock_app, producer_mock = get_mock_app(NatsBroker, NatsFastProducer)

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
                "subjectname",
                "--reply_to",
                "tester",
                "--correlation_id",
                "someId",
            ],
        )

        assert result.exit_code == 0

        assert producer_mock.publish.call_args.args[0] == "hello world"
        assert producer_mock.publish.call_args.kwargs == IsPartialDict(
            subject="subjectname",
            reply_to="tester",
            correlation_id="someId",
        )


@require_aiopika
def test_publish_command_with_rabbit_options(runner):
    from faststream.rabbit import RabbitBroker
    from faststream.rabbit.publisher.producer import AioPikaFastProducer

    mock_app, producer_mock = get_mock_app(RabbitBroker, AioPikaFastProducer)

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
            ],
        )

        assert result.exit_code == 0

        assert producer_mock.publish.call_args.args[0] == "hello world"
        assert producer_mock.publish.call_args.kwargs == IsPartialDict(
            {
                "correlation_id": "someId",
            }
        )


@require_nats
def test_publish_nats_request_command(runner: CliRunner):
    from faststream.nats import NatsBroker
    from faststream.nats.publisher.producer import NatsFastProducer

    mock_app, producer_mock = get_mock_app(NatsBroker, NatsFastProducer)

    with patch(
        "faststream._internal.cli.main.import_from_string",
        return_value=(None, mock_app),
    ):
        runner.invoke(
            faststream_app,
            [
                "publish",
                "fastream:app",
                "hello world",
                "--subject",
                "subjectname",
                "--rpc",
                "--timeout",
                "1.0",
            ],
        )

        assert producer_mock.request.call_args.args[0] == "hello world"
        assert producer_mock.request.call_args.kwargs == IsPartialDict(
            subject="subjectname",
            timeout=1.0,
        )
