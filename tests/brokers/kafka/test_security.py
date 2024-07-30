from contextlib import contextmanager
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@contextmanager
def _patch_aio_producer() -> Tuple[MagicMock, MagicMock]:
    try:
        producer = MagicMock(return_value=AsyncMock())

        with patch(
            "aiokafka.AIOKafkaProducer",
            new=producer,
        ):
            yield producer
    finally:
        pass


@pytest.mark.kafka()
@pytest.mark.asyncio()
async def test_gssapi():
    from docs.docs_src.kafka.security.sasl_gssapi import (
        broker as gssapi_broker,
    )

    with _patch_aio_producer() as producer:
        async with gssapi_broker:
            producer_call_kwargs = producer.call_args.kwargs

            call_kwargs = {
                "sasl_mechanism": "GSSAPI",
                "security_protocol": "SASL_SSL",
            }

            assert call_kwargs.items() <= producer_call_kwargs.items()
