from docs.docs_src.getting_started.asyncapi.asyncapi_customization.custom_broker import (
    app,
)
from faststream.specification.asyncapi.generate import get_app_schema


def test_broker_customization():
    schema = get_app_schema(app, version="2.6.0").to_jsonable()

    assert schema["servers"] == {
        "development": {
            "url": "non-sensitive-url:9092",
            "protocol": "kafka",
            "description": "Kafka broker running locally",
            "protocolVersion": "auto",
        }
    }
