from faststream import Context, ContextRepo, FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

predictions = broker.publisher("predictions_topic")


def multiply(x: float) -> float:
    return x * 2


@app.on_startup
async def setup_model(logger: Logger, context: ContextRepo):
    # Load the ML model
    logger.info("Loading the model...")
    context.set_global("ml_models", {"multiply_model": multiply})  # fakt ML model


@app.on_shutdown
async def shutdown_model(logger: Logger, ml_models=Context()):
    # Clean up the ML models and release the resources
    logger.info("Exiting, clearing model dict...")
    ml_models.clear()


@predictions
@broker.subscriber("input_data_1")
async def on_input_data_1(msg: float, logger: Logger, ml_models=Context()) -> float:
    logger.info(f"{msg=}")

    result = ml_models["multiply_model"](msg)
    logger.info(f"{result=}")

    return result


@broker.subscriber("input_data_2")
async def on_input_data_2(msg: float, logger: Logger, ml_models=Context()) -> None:
    logger.info(f"{msg=}")

    result = ml_models["multiply_model"](msg)
    logger.info(f"{result=}")

    await predictions.publish(result)
