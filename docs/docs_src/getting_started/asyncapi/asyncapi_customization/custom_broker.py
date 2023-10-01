from faststream import FastStream
from faststream.kafka import KafkaBroker, KafkaMessage
from faststream.asyncapi.schema import Tag

broker = KafkaBroker("localhost:9092", description="Kafka broker running locally")
app = FastStream(broker)

@broker.publisher("output_data")
@broker.subscriber("input_data")
async def on_input_data(msg):
    # your processing logic
    pass
