import pytest

from faststream.kafka import TestKafkaBroker

from .app import Plant, broker, on_plant_growth


@broker.subscriber("sell_plant")
async def on_sell_plant(msg: int) -> None:
    pass


@broker.subscriber("still_growing")
async def on_still_growing(msg: int) -> None:
    pass


@pytest.mark.asyncio
async def test_sell_plant_is_called():
    async with TestKafkaBroker(broker):
        await broker.publish(
            Plant(plant_id=1, species="Orange", ready_to_sell=True), "plant_growth"
        )
        on_plant_growth.mock.assert_called_with(
            dict(Plant(plant_id=1, species="Orange", ready_to_sell=True))
        )

        on_sell_plant.mock.assert_called_with(1)
        on_still_growing.mock.assert_not_called()


@pytest.mark.asyncio
async def test_still_growing_is_calles():
    async with TestKafkaBroker(broker):
        await broker.publish(
            Plant(plant_id=1, species="Orange", ready_to_sell=False), "plant_growth"
        )
        on_plant_growth.mock.assert_called_with(
            dict(Plant(plant_id=1, species="Orange", ready_to_sell=False))
        )

        on_still_growing.mock.assert_called_with(1)
        on_sell_plant.mock.assert_not_called()
