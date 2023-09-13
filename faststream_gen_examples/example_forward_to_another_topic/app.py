from typing import Optional

from pydantic import BaseModel, Field

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Document(BaseModel):
    name: str = Field(..., examples=["doc_name.txt"], description="Name example")
    content: Optional[str] = Field(
        default=None, examples=["New content"], description="Content example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("document_backup")
@broker.subscriber("document")
async def on_document(msg: Document, logger: Logger) -> Document:
    logger.info(msg)
    return msg
