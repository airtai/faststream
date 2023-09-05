from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


ml_models = {}  # fake ML model

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

predictions = broker.publisher("predictions_topic")


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


@predictions
@broker.subscriber("input_data_1")
async def on_input_data_1(msg: float, logger: Logger) -> float:
    logger.info(f"{msg=}")

    result = ml_models["multiply_model"](msg)
    logger.info(f"{result=}")
    
    return result


@broker.subscriber("input_data_2")
async def on_input_data_2(msg: float, logger: Logger) -> None:
    logger.info(f"{msg=}")

    result = ml_models["multiply_model"](msg)
    logger.info(f"{result=}")
    
    await predictions.publish(result)
