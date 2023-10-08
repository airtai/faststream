from docs.docs_src.getting_started.asyncapi.asyncapi_customization.custom_handler import (
    app,
)
from faststream.asyncapi.generate import get_app_schema


def test_handler_customization():
    schema = get_app_schema(app).to_jsonable()

    assert schema["channels"] == {
        "input_data:OnInputData": {
            "bindings": {"kafka": {"bindingVersion": "0.4.0", "topic": "input_data"}},
            "description": "My subscriber " "description",
            "servers": ["development"],
            "subscribe": {
                "message": {
                    "$ref": "#/components/messages/input_data:OnInputData:Message"
                }
            },
        },
        "output_data:Publisher": {
            "bindings": {"kafka": {"bindingVersion": "0.4.0", "topic": "output_data"}},
            "description": "My publisher " "description",
            "publish": {
                "message": {
                    "$ref": "#/components/messages/output_data:Publisher:Message"
                }
            },
            "servers": ["development"],
        },
    }
