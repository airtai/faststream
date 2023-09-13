import ssl
from typing import Optional

from pydantic import BaseModel, Field

from faststream import FastStream, Logger
from faststream.broker.security import SASLPlaintext
from faststream.kafka import KafkaBroker


class Document(BaseModel):
    name: str = Field(..., examples=["doc_name.txt"], description="Name example")
    content: Optional[str] = Field(
        default=None, examples=["New content"], description="Content example"
    )


ssl_context = ssl.create_default_context()
security = SASLPlaintext(ssl_context=ssl_context, username="admin", password="admin")

broker = KafkaBroker("localhost:9092", security=security)
app = FastStream(broker)


@broker.subscriber("document")
async def on_document(msg: Document, logger: Logger):
    """
    Processes a message from the 'document' topic and publishes the same message to the 'document_backup' topic.

    Instructions:
    1. Consume a message from 'document' topic.

    """
    raise NotImplementedError()
