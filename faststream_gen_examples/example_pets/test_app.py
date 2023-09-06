import pytest

from faststream.kafka import TestKafkaBroker

from .app import Pet, broker, on_new_pet


@broker.subscriber("notify_adopters")
async def on_notify_adopters(msg: Pet) -> None:
    pass


@pytest.mark.asyncio
async def test_app():
    async with TestKafkaBroker(broker):
        await broker.publish(Pet(pet_id=2, species="Dog", age=2), "new_pet")
        on_new_pet.mock.assert_called_with(dict(Pet(pet_id=2, species="Dog", age=2)))
        on_notify_adopters.mock.assert_called_with(
            dict(Pet(pet_id=2, species="Dog", age=2))
        )
