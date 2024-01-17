from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from faststream import FastStream
from faststream.cli.main import cli as faststream_app
from faststream.confluent import KafkaBroker as ConfluentBroker
from faststream.confluent.producer import AsyncConfluentFastProducer
from faststream.kafka import KafkaBroker
from faststream.kafka.producer import AioKafkaFastProducer
from faststream.nats import NatsBroker
from faststream.nats.producer import NatsFastProducer
from faststream.rabbit import RabbitBroker
from faststream.rabbit.producer import AioPikaFastProducer
from faststream.redis import RedisBroker
from faststream.redis.producer import RedisFastProducer

# Initialize the CLI runner
runner = CliRunner()


@pytest.fixture()
def mock_app(request):
    app = FastStream()
    broker_type = request.param["broker_type"]
    producer_type = request.param["producer_type"]

    broker = broker_type()
    broker.connect = AsyncMock()

    mock_producer = AsyncMock(spec=producer_type)
    mock_producer.publish = AsyncMock()
    broker._producer = mock_producer

    app.broker = broker
    return app


@pytest.mark.parametrize("mock_app", [{"broker_type": RedisBroker, "producer_type": RedisFastProducer}], indirect=True)
def test_publish_command_with_redis_options(mock_app):
    with patch("faststream.cli.main.import_from_string", return_value=(None, mock_app)):
        mock_app.broker.connect()

        result = runner.invoke(faststream_app, [
            "publish",
            "fastream:app",
            "hello world",
            "--channel", "test channel",
            "--reply_to", "tester",
            "--list",  "0.1",
            "--stream", "stream url",
            "--correlation_id", "someId",
        ])

        assert result.exit_code == 0
        mock_app.broker._producer.publish.assert_awaited_once_with(
            message="hello world",
            channel="test channel",
            reply_to="tester",
            list="0.1",
            stream="stream url",
            correlation_id="someId",
            rpc=False,
        )


@pytest.mark.parametrize("mock_app", [{"broker_type": ConfluentBroker, "producer_type": AsyncConfluentFastProducer}], indirect=True)
def test_publish_command_with_confluent_options(mock_app):
    with patch("faststream.cli.main.import_from_string", return_value=(None, mock_app)):
        mock_app.broker.connect()
        result = runner.invoke(faststream_app, [
            "publish",
            "fastream:app",
            "hello world",
            "--topic", "confluent topic",
            "--correlation_id", "someId",
        ])

        assert result.exit_code == 0
        mock_app.broker._producer.publish.assert_awaited_once_with(
            message="hello world",
            topic="confluent topic",
            correlation_id="someId",
            rpc=False,
        )


@pytest.mark.parametrize("mock_app", [{"broker_type": KafkaBroker, "producer_type": AioKafkaFastProducer}], indirect=True)
def test_publish_command_with_kafka_options(mock_app):
    with patch("faststream.cli.main.import_from_string", return_value=(None, mock_app)):
        mock_app.broker.connect()
        result = runner.invoke(faststream_app, [
            "publish",
            "fastream:app",
            "hello world",
            "--topic", "kafka topic",
            "--correlation_id", "someId",
        ])

        assert result.exit_code == 0
        mock_app.broker._producer.publish.assert_awaited_once_with(
            message="hello world",
            topic="kafka topic",
            correlation_id="someId",
            rpc=False,
        )


@pytest.mark.parametrize("mock_app", [{"broker_type": NatsBroker, "producer_type": NatsFastProducer}], indirect=True)
def test_publish_command_with_nats_options(mock_app):
    with patch("faststream.cli.main.import_from_string", return_value=(None, mock_app)):
        mock_app.broker.connect()
        result = runner.invoke(faststream_app, [
            "publish",
            "fastream:app",
            "hello world",
            "--subject", "nats subject",
            "--reply_to", "tester",
            "--correlation_id", "someId",
        ])

        assert result.exit_code == 0
        mock_app.broker._producer.publish.assert_awaited_once_with(
            message="hello world",
            subject="nats subject",
            reply_to="tester",
            correlation_id="someId",
            rpc=False,
        )


@pytest.mark.parametrize("mock_app", [{"broker_type": RabbitBroker, "producer_type": AioPikaFastProducer}], indirect=True)
def test_publish_command_with_rabbit_options(mock_app):
    with patch("faststream.cli.main.import_from_string", return_value=(None, mock_app)):
        mock_app.broker.connect()
        result = runner.invoke(faststream_app, [
            "publish",
            "fastream:app",
            "hello world",
            "--correlation_id", "someId",
            "--raise_timeout", "True",
        ])

        assert result.exit_code == 0
        mock_app.broker._producer.publish.assert_awaited_once_with(
            message="hello world",
            correlation_id="someId",
            raise_timeout="True",
            rpc=False,
        )
