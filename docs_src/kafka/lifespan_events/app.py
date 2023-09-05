from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


ml_models = {}  # fake ML model

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

to_output_data = broker.publisher("output_data")


def multiply(x: float) -> float:
    return x * 2

@app.on_startup
async def setup_model():
    # Load the ML model
    print("Loading the model!")
    ml_models["multiply_model"] = multiply


@app.on_shutdown
async def shutdown_model():
    # Clean up the ML models and release the resources
    print("Exiting, clearing model dict!")
    ml_models.clear()


@to_output_data
@broker.subscriber("input_data_1")
async def predict_1(msg: float, logger: Logger) -> float:
    logger.info(f"{msg=}")

    result = ml_models["multiply_model"](msg)
    logger.info(f"{result=}")
    
    return result


@broker.subscriber("input_data_2")
async def predict_2(msg: float, logger: Logger) -> None:
    logger.info(f"{msg=}")

    result = ml_models["multiply_model"](msg)
    logger.info(f"{result=}")
    
    await to_output_data.publish(result)


@broker.subscriber("output_data")
async def on_output_data(msg: float, logger: Logger):
    pass

import pytest

from faststream.kafka import TestKafkaBroker
from faststream import TestApp as T

# from .basic import DataBasic, broker, on_input_data

@pytest.mark.asyncio
async def test_lifespan_with_publisher_decorator():
    async with TestKafkaBroker(broker):
        async with T(app):
            
            await broker.publish(2, "input_data_2")
            # await predict_1.wait_call(2)
        

@pytest.mark.asyncio
async def test_lifespan_with_await_inside_subscriber():


    async with TestKafkaBroker(broker):
        async with T(app):
            
            await broker.publish(2, "input_data_2")


# @pytest.mark.asyncio
# async def test_lifespan_with_await_inside_subscriber_without_tester():
#     # async with TestKafkaBroker(broker):
#     async with T(app):
        
#         await broker.publish(2, "input_data_2")