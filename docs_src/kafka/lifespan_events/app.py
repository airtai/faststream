from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

# from sklearn.datasets import load_iris
# from sklearn.linear_model import LogisticRegression
from contextlib import asynccontextmanager


ml_models = {}

# @asynccontextmanager
# async def lifespan(app: FastKafka):
#     # Load the ML model
#     print("Loading the model!")
#     X, y = load_iris(return_X_y=True)
#     ml_models["iris_predictor"] = LogisticRegression(random_state=0, max_iter=500).fit(X, y)
#     yield
#     # Clean up the ML models and release the resources
    
#     print("Exiting, clearing model dict!")
#     ml_models.clear()
    


class DataBasic(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


ml_models = {}  # fake ML model

def multiply(x: float):
    return x * 2

@app.on_startup
async def setup_model():
    # Load the ML model
    print("Loading the model!")
    ml_models["multiply_model"] = multiply
    # Load the ML model
    # ml_models["answer_to_everything"] = fake_answer_to_everything_ml_model
    # context.set_global("model", ml_models)
    pass

@app.on_shutdown
async def shutdown_model():
    # Clean up the ML models and release the resources
    print("Exiting, clearing model dict!")
    ml_models.clear()

@broker.subscriber("test")
async def predict(msg: float, logger: Logger):
    logger.info(f"{msg=}")
    result = ml_models["multiply_model"](msg)
    logger.info(f"{result=}")
    # result = model["answer_to_everything"](x)
    # return {"result": result}




import pytest

from faststream.kafka import TestKafkaBroker
from faststream import TestApp

# from .basic import DataBasic, broker, on_input_data

@broker.subscriber("output_data")
async def on_output_data(msg: DataBasic):
    pass

@pytest.mark.asyncio
async def test_base_app():
        # pass
    async with TestKafkaBroker(broker):
        async with TestApp(app):
            await broker.publish(2, "test")
        
