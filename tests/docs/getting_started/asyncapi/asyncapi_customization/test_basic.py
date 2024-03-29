from docs.docs_src.getting_started.asyncapi.asyncapi_customization.basic import app
from faststream.asyncapi.generate import get_app_schema


def test_basic_customization():
    schema = get_app_schema(app).to_jsonable()
    assert schema == {
        "asyncapi": "2.6.0",
        "channels": {
            "input_data:OnInputData": {
                "bindings": {
                    "kafka": {"bindingVersion": "0.4.0", "topic": "input_data"}
                },
                "servers": ["development"],
                "subscribe": {
                    "message": {
                        "$ref": "#/components/messages/input_data:OnInputData:Message"
                    }
                },
            },
            "output_data:Publisher": {
                "bindings": {
                    "kafka": {"bindingVersion": "0.4.0", "topic": "output_data"}
                },
                "publish": {
                    "message": {
                        "$ref": "#/components/messages/output_data:Publisher:Message"
                    }
                },
                "servers": ["development"],
            },
        },
        "components": {
            "messages": {
                "input_data:OnInputData:Message": {
                    "correlationId": {"location": "$message.header#/correlation_id"},
                    "payload": {
                        "$ref": "#/components/schemas/OnInputData:Message:Payload"
                    },
                    "title": "input_data:OnInputData:Message",
                },
                "output_data:Publisher:Message": {
                    "correlationId": {"location": "$message.header#/correlation_id"},
                    "payload": {
                        "$ref": "#/components/schemas/output_data:PublisherPayload"
                    },
                    "title": "output_data:Publisher:Message",
                },
            },
            "schemas": {
                "OnInputData:Message:Payload": {"title": "OnInputData:Message:Payload"},
                "output_data:PublisherPayload": {},
            },
        },
        "defaultContentType": "application/json",
        "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
        "servers": {
            "development": {
                "protocol": "kafka",
                "protocolVersion": "auto",
                "url": "localhost:9092",
            }
        },
    }
