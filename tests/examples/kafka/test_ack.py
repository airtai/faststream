from unittest.mock import patch

import pytest

from examples.kafka.ack_after_process import app, broker
from faststream.kafka import TestApp, TestKafkaBroker
from faststream.kafka.message import KafkaMessage
from tests.tools import spy_decorator


@pytest.mark.asyncio
async def test_ack():
    with patch.object(KafkaMessage, "ack", spy_decorator(KafkaMessage.ack)) as m:
        async with TestKafkaBroker(broker), TestApp(app):
            m.mock.assert_called_once()
