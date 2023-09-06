import pytest
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream._compat import model_to_json
from faststream.kafka import KafkaBroker, TestKafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


@broker.subscriber("input_data")
async def handle_data(msg: Data, logger: Logger) -> None:
    logger.info(f"handle_data({msg=})")


@pytest.mark.asyncio
async def test_raw_publish():
    async with TestKafkaBroker(broker):
        msg = Data(data=0.5)

        await broker.publish(
            model_to_json(msg),
            "input_data",
            headers={"content-type": "application/json"},
        )

        handle_data.mock.assert_called_once_with(dict(msg))
