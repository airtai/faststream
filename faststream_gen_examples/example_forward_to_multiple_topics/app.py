from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("output_1")
@broker.publisher("output_2")
@broker.publisher("output_3")
@broker.subscriber("input")
async def on_input(msg: str, logger: Logger) -> str:
    logger.info(msg)
    return msg
