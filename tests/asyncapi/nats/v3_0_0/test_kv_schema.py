from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.asyncapi.version import AsyncAPIVersion
from faststream.nats import NatsBroker


def test_kv_schema():
    broker = NatsBroker()

    @broker.subscriber("test", kv_watch="test")
    async def handle(): ...

    schema = get_app_schema(FastStream(broker, asyncapi_version=AsyncAPIVersion.v3_0)).to_jsonable()

    assert schema["channels"] == {}
