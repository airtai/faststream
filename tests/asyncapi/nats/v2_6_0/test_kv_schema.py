from faststream import FastStream
from faststream.specification.asyncapi.generate import get_app_schema
from faststream.nats import NatsBroker


def test_kv_schema():
    broker = NatsBroker()

    @broker.subscriber("test", kv_watch="test")
    async def handle(): ...

    schema = get_app_schema(FastStream(broker)).to_jsonable()

    assert schema["channels"] == {}
