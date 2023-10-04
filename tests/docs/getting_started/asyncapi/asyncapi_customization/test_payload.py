from docs.docs_src.getting_started.asyncapi.asyncapi_customization.payload_info import (
    app,
)
from faststream.asyncapi.generate import get_app_schema


def test_payload_customization():
    schema = get_app_schema(app).to_jsonable()

    assert schema["components"] == {
        "messages": {
            "input_data:OnInputData:Message": {
                "title": "input_data:OnInputData:Message",
                "correlationId": {"location": "$message.header#/correlation_id"},
                "payload": {"$ref": "#/components/schemas/DataBasic"},
            },
            "output_data:Message": {
                "title": "output_data:Message",
                "correlationId": {"location": "$message.header#/correlation_id"},
                "payload": {"$ref": "#/components/schemas/DataBasic"},
            },
        },
        "schemas": {
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
        },
    }
