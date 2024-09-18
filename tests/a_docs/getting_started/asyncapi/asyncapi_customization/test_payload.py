from docs.docs_src.getting_started.asyncapi.asyncapi_customization.custom_info import docs_obj
from docs.docs_src.getting_started.asyncapi.asyncapi_customization.payload_info import app, docs_obj

from faststream.specification.asyncapi import AsyncAPI


def test_payload_customization():
    schema = docs_obj.jsonable()

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
