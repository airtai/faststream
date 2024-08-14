from docs.docs_src.getting_started.asyncapi.asyncapi_customization.custom_handler import (
    app,
)
from faststream.specification.asyncapi.generate import get_app_schema


def test_handler_customization():
    schema = get_app_schema(app).to_jsonable()

    assert schema["channels"] == {
        "input_data:Consume": {
            "description": "Consumer function\n\n    Args:\n        msg: input msg\n    ",
            "servers": ["development"],
            "bindings": {"kafka": {"topic": "input_data", "bindingVersion": "0.4.0"}},
            "subscribe": {
                "message": {"$ref": "#/components/messages/input_data:Consume:Message"}
            },
        },
        "output_data:Produce": {
            "description": "My publisher description",
            "servers": ["development"],
            "bindings": {"kafka": {"topic": "output_data", "bindingVersion": "0.4.0"}},
            "publish": {
                "message": {"$ref": "#/components/messages/output_data:Produce:Message"}
            },
        },
    }
