from docs.docs_src.getting_started.asyncapi.asyncapi_customization.basic import app
from faststream.asyncapi.generate import get_app_schema


def test_basic_customization():
    schema = get_app_schema(app).to_jsonable()
    assert schema == {
        "asyncapi": "2.6.0",
        "defaultContentType": "application/json",
        "info": {"title": "FastStream", "version": "0.1.0", "description": ""},
        "servers": {
            "development": {
                "url": "localhost:9092",
                "protocol": "kafka",
                "protocolVersion": "auto",
            }
        },
        "channels": {
            "input_data:OnInputData": {
                "servers": ["development"],
                "bindings": {
                    "kafka": {"topic": "input_data", "bindingVersion": "0.4.0"}
                },
                "subscribe": {
                    "message": {
                        "$ref": "#/components/messages/input_data:OnInputData:Message"
                    }
                },
            },
            "output_data": {
                "servers": ["development"],
                "bindings": {
                    "kafka": {"topic": "output_data", "bindingVersion": "0.4.0"}
                },
                "publish": {
                    "message": {"$ref": "#/components/messages/output_data:Message"}
                },
            },
        },
        "components": {
            "messages": {
                "input_data:OnInputData:Message": {
                    "title": "input_data:OnInputData:Message",
                    "correlationId": {"location": "$message.header#/correlation_id"},
                    "payload": {
                        "$ref": "#/components/schemas/input_data:OnInputData:Message:Msg:Payload"
                    },
                },
                "output_data:Message": {
                    "title": "output_data:Message",
                    "correlationId": {"location": "$message.header#/correlation_id"},
                    "payload": {"$ref": "#/components/schemas/output_dataPayload"},
                },
            },
            "schemas": {
                "input_data:OnInputData:Message:Msg:Payload": {
                    "title": "input_data:OnInputData:Message:Msg:Payload"
                },
                "output_dataPayload": {},
            },
        },
    }
