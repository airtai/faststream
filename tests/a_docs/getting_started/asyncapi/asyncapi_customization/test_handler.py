from docs.docs_src.getting_started.asyncapi.asyncapi_customization.custom_handler import (
    docs_obj,
)


def test_handler_customization():
    schema = docs_obj.to_jsonable()

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
