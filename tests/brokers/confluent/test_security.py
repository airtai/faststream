from contextlib import contextmanager
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from docs.docs_src.confluent.security.ssl_warning import test_without_ssl_warning
from faststream.exceptions import SetupError

__all__ = ["test_without_ssl_warning"]


@contextmanager
def patch_aio_consumer_and_producer() -> Tuple[MagicMock, MagicMock]:
    try:
        producer = MagicMock(return_value=AsyncMock())

        with patch(
            "faststream.confluent.broker.broker.AsyncConfluentProducer",
            new=producer,
        ):
            yield producer
    finally:
        pass


@pytest.mark.asyncio()
@pytest.mark.confluent()
async def test_base_security():
    from docs.docs_src.confluent.security.basic import broker as basic_broker

    with patch_aio_consumer_and_producer() as producer:
        async with basic_broker:
            producer_call_kwargs = producer.call_args.kwargs

            call_kwargs = {}

            assert call_kwargs.items() <= producer_call_kwargs.items()


@pytest.mark.asyncio()
@pytest.mark.confluent()
async def test_base_security_pass_ssl_context():
    import ssl

    from faststream.confluent import KafkaBroker
    from faststream.security import BaseSecurity

    ssl_context = ssl.create_default_context()
    security = BaseSecurity(ssl_context=ssl_context)

    basic_broker = KafkaBroker("localhost:9092", security=security)

    with patch_aio_consumer_and_producer(), pytest.raises(
        SetupError, match="not supported"
    ) as e:
        async with basic_broker:
            pass

    assert (
        str(e.value)
        == "ssl_context in not supported by confluent-kafka-python, please use config instead."
    )


@pytest.mark.asyncio()
@pytest.mark.confluent()
async def test_scram256():
    from docs.docs_src.confluent.security.sasl_scram256 import (
        broker as scram256_broker,
    )

    with patch_aio_consumer_and_producer() as producer:
        async with scram256_broker:
            producer_call_kwargs = producer.call_args.kwargs

            call_kwargs = {}
            call_kwargs["sasl_mechanism"] = "SCRAM-SHA-256"
            call_kwargs["sasl_plain_username"] = "admin"
            call_kwargs["sasl_plain_password"] = "password"  # pragma: allowlist secret
            call_kwargs["security_protocol"] = "SASL_SSL"

            assert call_kwargs.items() <= producer_call_kwargs.items()

            assert (
                producer_call_kwargs["security_protocol"]
                == call_kwargs["security_protocol"]
            )


@pytest.mark.asyncio()
@pytest.mark.confluent()
async def test_scram512():
    from docs.docs_src.confluent.security.sasl_scram512 import (
        broker as scram512_broker,
    )

    with patch_aio_consumer_and_producer() as producer:
        async with scram512_broker:
            producer_call_kwargs = producer.call_args.kwargs

            call_kwargs = {}
            call_kwargs["sasl_mechanism"] = "SCRAM-SHA-512"
            call_kwargs["sasl_plain_username"] = "admin"
            call_kwargs["sasl_plain_password"] = "password"  # pragma: allowlist secret
            call_kwargs["security_protocol"] = "SASL_SSL"

            assert call_kwargs.items() <= producer_call_kwargs.items()

            assert (
                producer_call_kwargs["security_protocol"]
                == call_kwargs["security_protocol"]
            )


@pytest.mark.asyncio()
@pytest.mark.confluent()
async def test_plaintext():
    from docs.docs_src.confluent.security.plaintext import (
        broker as plaintext_broker,
    )

    with patch_aio_consumer_and_producer() as producer:
        async with plaintext_broker:
            producer_call_kwargs = producer.call_args.kwargs

            call_kwargs = {}
            call_kwargs["sasl_mechanism"] = "PLAIN"
            call_kwargs["sasl_plain_username"] = "admin"
            call_kwargs["sasl_plain_password"] = "password"  # pragma: allowlist secret
            call_kwargs["security_protocol"] = "SASL_SSL"

            assert call_kwargs.items() <= producer_call_kwargs.items()

            assert (
                producer_call_kwargs["security_protocol"]
                == call_kwargs["security_protocol"]
            )
