from docs.docs_src.getting_started.asyncapi.asyncapi_customization.custom_handler import (
    app,
)
from faststream.asyncapi.generate import get_app_schema


def test_handler_customization():
    schema = get_app_schema(app).to_jsonable()

    assert schema["channels"] == {
        "input_data/OnInputData": {
            "description": "My subscriber description",
            "servers": ["development"],
            "bindings": {"kafka": {"topic": "input_data", "bindingVersion": "0.4.0"}},
            "subscribe": {
                "message": {
                    "$ref": "#/components/messages/input_data/OnInputData/Message"
                }
            },
        },
        "output_data": {
            "description": "My publisher description",
            "servers": ["development"],
            "bindings": {"kafka": {"topic": "output_data", "bindingVersion": "0.4.0"}},
            "publish": {
                "message": {"$ref": "#/components/messages/output_data/Message"}
            },
        },
    }
