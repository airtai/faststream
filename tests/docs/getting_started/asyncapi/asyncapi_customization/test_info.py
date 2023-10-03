from docs.docs_src.getting_started.asyncapi.asyncapi_customization.custom_info import (
    app,
)
from faststream.asyncapi.generate import get_app_schema


def test_broker_customization():
    schema = get_app_schema(app).to_jsonable()

    assert schema == {
        "asyncapi": "2.6.0",
        "defaultContentType": "application/json",
        "info": {
            "title": "My App",
            "version": "1.0.0",
            "description": "Test description",
            "termsOfService": "https://my-terms.com/",
            "contact": {"name": "support", "url": "https://help.com/"},
            "license": {"name": "MIT", "url": "https://opensource.org/license/mit/"},
        },
        "servers": {
            "development": {
                "url": "localhost:9092",
                "protocol": "kafka",
                "protocolVersion": "auto",
            }
        },
        "channels": {
            "OnInputData": {
                "servers": ["development"],
                "bindings": {
                    "kafka": {"topic": "input_data", "bindingVersion": "0.4.0"}
                },
                "subscribe": {
                    "message": {"$ref": "#/components/messages/OnInputDataMessage"}
                },
            },
            "Output_DataPublisher": {
                "servers": ["development"],
                "bindings": {
                    "kafka": {"topic": "output_data", "bindingVersion": "0.4.0"}
                },
                "publish": {
                    "message": {
                        "$ref": "#/components/messages/Output_DataPublisherMessage"
                    }
                },
            },
        },
        "components": {
            "messages": {
                "OnInputDataMessage": {
                    "title": "OnInputDataMessage",
                    "correlationId": {"location": "$message.header#/correlation_id"},
                    "payload": {"$ref": "#/components/schemas/OnInputDataMsgPayload"},
                },
                "Output_DataPublisherMessage": {
                    "title": "Output_DataPublisherMessage",
                    "correlationId": {"location": "$message.header#/correlation_id"},
                    "payload": {
                        "$ref": "#/components/schemas/Output_DataPublisherPayload"
                    },
                },
            },
            "schemas": {
                "OnInputDataMsgPayload": {"title": "OnInputDataMsgPayload"},
                "Output_DataPublisherPayload": {},
            },
        },
    }
