import ssl
from typing import Optional

from pydantic import BaseModel, Field

from faststream import Logger
from faststream.broker.security import BaseSecurity
from faststream.kafka import KafkaBroker


class Document(BaseModel):
    name: str = Field(..., examples=["doc_name.txt"], description="Name example")
    content: Optional[str] = Field(
        default=None, examples=["New content"], description="Content example"
    )


ssl_context = ssl.create_default_context()
security = BaseSecurity(ssl_context=ssl_context)

broker = KafkaBroker("localhost:9092", security=security)


@broker.publisher("document_backup")
@broker.subscriber("document")
async def on_document(msg: Document, logger: Logger) -> Document:
    logger.info(msg)
    return msg
