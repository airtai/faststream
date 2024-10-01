from faststream.nats import NatsBroker
from faststream.specification.asyncapi import AsyncAPI


def test_obj_schema():
    broker = NatsBroker()

    @broker.subscriber("test", obj_watch=True)
    async def handle(): ...

    schema = AsyncAPI(broker, schema_version="2.6.0").to_jsonable()

    assert schema["channels"] == {}
