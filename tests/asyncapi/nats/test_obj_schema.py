from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.nats import NatsBroker


def test_obj_schema():
    broker = NatsBroker()

    @broker.subscriber("test", obj_watch=True)
    async def handle(): ...

    schema = get_app_schema(FastStream(broker)).to_jsonable()

    assert schema["channels"] == {}
