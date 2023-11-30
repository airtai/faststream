import pytest
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream._compat import model_to_json
from faststream.redis import RedisBroker, TestRedisBroker


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = RedisBroker("localhost:6379")
app = FastStream(broker)


@broker.subscriber("input_data")
async def on_input_data(msg: Data, logger: Logger) -> Data:
    logger.info(f"on_input_data({msg=})")


@pytest.mark.asyncio
async def test_raw_publish():
    async with TestRedisBroker(broker):
        msg = Data(data=0.5)

        await broker.publish(
            model_to_json(msg),
            "input_data",
            headers={"content-type": "application/json"},
        )

        on_input_data.mock.assert_called_once_with(dict(msg))
