from faststream import FastStream
from faststream.nats import NatsBroker
from faststream.specification.asyncapi.generate import get_app_schema
from faststream.specification.asyncapi.version import AsyncAPIVersion


def test_kv_schema():
    broker = NatsBroker()

    @broker.subscriber("test", kv_watch="test")
    async def handle(): ...

    schema = get_app_schema(FastStream(broker), version=AsyncAPIVersion.v2_6).to_jsonable()

    assert schema["channels"] == {}
