import ssl
from contextlib import contextmanager
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from docs.docs_src.kafka.security_without_ssl.example import test_without_ssl_warning

__all__ = ["test_without_ssl_warning"]


@contextmanager
def patch_aio_consumer_and_producer() -> Tuple[MagicMock, MagicMock]:
    try:
        consumer = MagicMock(return_value=AsyncMock())
        producer = MagicMock(return_value=MagicMock())

        with patch("aiokafka.AIOKafkaConsumer", new=consumer):
            with patch("faststream.kafka.client.Producer", new=producer):
                yield consumer, producer
    finally:
        pass


@pytest.mark.asyncio
@pytest.mark.confluent_kafka
async def test_base_security():
    with patch_aio_consumer_and_producer() as (consumer, producer):
        from docs.docs_src.kafka.basic_security.confluent_kafka_app import (
            broker as basic_broker,
        )

        async with basic_broker:
            await basic_broker.start()

        consumer_call_kwargs = consumer.call_args.kwargs
        producer_call_config_arg = producer.call_args[0][0]

        call_kwargs = {}
        call_kwargs["security_protocol"] = "SSL"

        confluent_config = {".".join(k.split("_")): v for k, v in call_kwargs.items()}
        confluent_config["security.protocol"] = confluent_config[
            "security.protocol"
        ].lower()

        assert call_kwargs.items() <= consumer_call_kwargs.items()
        assert confluent_config.items() <= producer_call_config_arg.items()

        assert type(consumer_call_kwargs["ssl_context"]) == ssl.SSLContext
        assert (
            producer_call_config_arg["security.protocol"]
            == confluent_config["security.protocol"]
        )


@pytest.mark.asyncio
@pytest.mark.confluent_kafka
async def test_scram256():
    with patch_aio_consumer_and_producer() as (consumer, producer):
        from docs.docs_src.kafka.sasl_scram256_security.confluent_kafka_app import (
            broker as scram256_broker,
        )

        async with scram256_broker:
            await scram256_broker.start()

        consumer_call_kwargs = consumer.call_args.kwargs
        producer_call_config_arg = producer.call_args[0][0]

        call_kwargs = {}
        call_kwargs["sasl_mechanism"] = "SCRAM-SHA-256"
        call_kwargs["sasl_plain_username"] = "admin"
        call_kwargs["sasl_plain_password"] = "password"  # pragma: allowlist secret
        call_kwargs["security_protocol"] = "SASL_SSL"

        confluent_config = {".".join(k.split("_")): v for k, v in call_kwargs.items()}
        confluent_config["security.protocol"] = confluent_config[
            "security.protocol"
        ].lower()
        confluent_config["sasl.username"] = confluent_config.pop("sasl.plain.username")
        confluent_config["sasl.password"] = confluent_config.pop("sasl.plain.password")

        assert call_kwargs.items() <= consumer_call_kwargs.items()
        assert confluent_config.items() <= producer_call_config_arg.items()

        assert type(consumer_call_kwargs["ssl_context"]) == ssl.SSLContext
        assert (
            producer_call_config_arg["security.protocol"]
            == confluent_config["security.protocol"]
        )


@pytest.mark.asyncio
@pytest.mark.confluent_kafka
async def test_scram512():
    with patch_aio_consumer_and_producer() as (consumer, producer):
        from docs.docs_src.kafka.sasl_scram512_security.confluent_kafka_app import (
            broker as scram512_broker,
        )

        async with scram512_broker:
            await scram512_broker.start()

        consumer_call_kwargs = consumer.call_args.kwargs
        producer_call_config_arg = producer.call_args[0][0]

        call_kwargs = {}
        call_kwargs["sasl_mechanism"] = "SCRAM-SHA-512"
        call_kwargs["sasl_plain_username"] = "admin"
        call_kwargs["sasl_plain_password"] = "password"  # pragma: allowlist secret
        call_kwargs["security_protocol"] = "SASL_SSL"

        confluent_config = {".".join(k.split("_")): v for k, v in call_kwargs.items()}
        confluent_config["security.protocol"] = confluent_config[
            "security.protocol"
        ].lower()
        confluent_config["sasl.username"] = confluent_config.pop("sasl.plain.username")
        confluent_config["sasl.password"] = confluent_config.pop("sasl.plain.password")

        assert call_kwargs.items() <= consumer_call_kwargs.items()
        assert confluent_config.items() <= producer_call_config_arg.items()

        assert type(consumer_call_kwargs["ssl_context"]) == ssl.SSLContext
        assert (
            producer_call_config_arg["security.protocol"]
            == confluent_config["security.protocol"]
        )


@pytest.mark.asyncio
@pytest.mark.confluent_kafka
async def test_plaintext():
    with patch_aio_consumer_and_producer() as (consumer, producer):
        from docs.docs_src.kafka.plaintext_security.confluent_kafka_app import (
            broker as plaintext_broker,
        )

        async with plaintext_broker:
            await plaintext_broker.start()

        consumer_call_kwargs = consumer.call_args.kwargs
        producer_call_config_arg = producer.call_args[0][0]

        call_kwargs = {}
        call_kwargs["sasl_mechanism"] = "PLAIN"
        call_kwargs["sasl_plain_username"] = "admin"
        call_kwargs["sasl_plain_password"] = "password"  # pragma: allowlist secret
        call_kwargs["security_protocol"] = "SASL_SSL"

        confluent_config = {".".join(k.split("_")): v for k, v in call_kwargs.items()}
        confluent_config["security.protocol"] = confluent_config[
            "security.protocol"
        ].lower()
        confluent_config["sasl.username"] = confluent_config.pop("sasl.plain.username")
        confluent_config["sasl.password"] = confluent_config.pop("sasl.plain.password")

        assert call_kwargs.items() <= consumer_call_kwargs.items()
        assert confluent_config.items() <= producer_call_config_arg.items()

        assert type(consumer_call_kwargs["ssl_context"]) == ssl.SSLContext
        assert (
            producer_call_config_arg["security.protocol"]
            == confluent_config["security.protocol"]
        )
