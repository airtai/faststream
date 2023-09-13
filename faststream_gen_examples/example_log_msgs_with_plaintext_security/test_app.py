import pytest

from faststream.kafka import TestKafkaBroker

from .app import Document, broker, on_document


@pytest.mark.asyncio
async def test_app():
    async with TestKafkaBroker(broker):
        await broker.publish(
            Document(name="doc.txt", content="Introduction to FastStream"), "document"
        )
        on_document.mock.assert_called_with(
            dict(Document(name="doc.txt", content="Introduction to FastStream"))
        )
