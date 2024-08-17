from docs.docs_src.getting_started.asyncapi.asyncapi_customization.payload_info import (
    app,
)
from faststream.specification.asyncapi.generate import get_app_schema
from faststream.specification.asyncapi.version import AsyncAPIVersion


def test_payload_customization():
    schema = get_app_schema(app, version=AsyncAPIVersion.v2_6).to_jsonable()

    assert schema["components"]["schemas"] == {
        "DataBasic": {
            "properties": {
                "data": {
                    "description": "Float data example",
                    "examples": [0.5],
                    "minimum": 0,
                    "title": "Data",
                    "type": "number",
                }
            },
            "required": ["data"],
            "title": "DataBasic",
            "type": "object",
        }
    }
