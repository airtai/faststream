import pytest
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import Logger
from faststream.kafka import KafkaBroker, TestKafkaBroker


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")

to_output_data = broker.publisher("output_data")


@to_output_data
@broker.subscriber("input_data")
async def on_input_data(msg: Data, logger: Logger) -> Data:
    logger.info(msg)
    return Data(data=msg.data + 1.0)


async def _test_with_broker(with_real: bool):
    @broker.subscriber("output_data")
    async def on_output_data(msg: Data):
        pass

    async with TestKafkaBroker(broker, with_real=with_real) as tester:
        await tester.publish(Data(data=0.2), "input_data")

        await on_output_data.wait_call(3)

        on_input_data.mock.assert_called_with(dict(Data(data=0.2)))
        to_output_data.mock.assert_called_with(dict(Data(data=1.2)))
        on_output_data.mock.assert_called_once_with(dict(Data(data=1.2)))


@pytest.mark.asyncio
async def test_with_fake_broker_1():
    await _test_with_broker(False)


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Reentrancy planned to be fixed in https://github.com/airtai/fastkafka/issues/556"
)
async def test_with_fake_broker_2():
    await _test_with_broker(False)


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Reentrancy planned to be fixed in https://github.com/airtai/fastkafka/issues/556"
)
async def test_with_real_broker_1():
    await _test_with_broker(True)


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Reentrancy planned to be fixed in https://github.com/airtai/fastkafka/issues/556"
)
async def test_with_real_broker_2():
    await _test_with_broker(True)


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Reentrancy planned to be fixed in https://github.com/airtai/fastkafka/issues/556"
)
async def test_with_fake_broker_3():
    await _test_with_broker(False)


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Reentrancy planned to be fixed in https://github.com/airtai/fastkafka/issues/556"
)
async def test_with_fake_broker_4():
    await _test_with_broker(False)
