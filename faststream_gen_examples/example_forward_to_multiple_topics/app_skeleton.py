from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("output_1")
@broker.publisher("output_2")
@broker.publisher("output_3")
@broker.subscriber("input")
async def on_input(msg: str, logger: Logger) -> str:
    """
    Processes a message from the 'input' topic and publishes the same message to the 'output_1', 'output_2' and 'output_3' topic.

    Instructions:
    1. Consume a message from 'input' topic.
    2. Publish the same message to 'output_1', 'output_2' and 'output_3' topic.
    """
    raise NotImplementedError()
