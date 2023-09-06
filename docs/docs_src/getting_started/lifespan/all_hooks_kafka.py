from faststream import ContextRepo, FastStream
from faststream.kafka import KafkaBroker
from faststream.kafka.annotations import KafkaBroker as BrokerAnnotation

app = FastStream(KafkaBroker("localhost:9092"))


@app.on_startup
def cli_run(  # sync or async function
    context: ContextRepo,  # get from global context
    env: str = ".env",  # get from CLI option `--env=...`
):
    context.set_global("use_env", env)


@app.after_startup
async def broker_available(
    broker: BrokerAnnotation,  # get from global context
):
    await broker.publish("Service started", topic="logs")


@app.on_shutdown
async def broker_still_available(
    broker: BrokerAnnotation,  # get from global context
):
    await broker.publish("Service stopped", topic="logs")


@app.after_shutdown
async def broker_stopped(
    broker: BrokerAnnotation,  # get from global context
):
    assert broker._connection is None
