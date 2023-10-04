import ssl
from copy import deepcopy

from faststream.app import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.broker.security import (
    BaseSecurity,
    SASLPlaintext,
    SASLScram256,
    SASLScram512,
)
from faststream.kafka.annotations import KafkaBroker

basic_schema = {
    "asyncapi": "2.6.0",
    "defaultContentType": "application/json",
    "info": {"title": "FastStream", "version": "0.1.0", "description": ""},
    "servers": {
        "development": {
            "url": "localhost:9092",
            "protocol": "kafka-secure",
            "protocolVersion": "auto",
            "security": [],
        }
    },
    "channels": {
        "test_1/TestTopic": {
            "servers": ["development"],
            "bindings": {"kafka": {"topic": "test_1", "bindingVersion": "0.4.0"}},
            "subscribe": {
                "message": {"$ref": "#/components/messages/test_1/TestTopic/Message"}
            },
        },
        "test_2": {
            "servers": ["development"],
            "bindings": {"kafka": {"topic": "test_2", "bindingVersion": "0.4.0"}},
            "publish": {"message": {"$ref": "#/components/messages/test_2/Message"}},
        },
    },
    "components": {
        "messages": {
            "test_1/TestTopic/Message": {
                "title": "test_1/TestTopic/Message",
                "correlationId": {"location": "$message.header#/correlation_id"},
                "payload": {
                    "$ref": "#/components/schemas/test_1/TestTopic/Message/Msg/Payload"
                },
            },
            "test_2/Message": {
                "title": "test_2/Message",
                "correlationId": {"location": "$message.header#/correlation_id"},
                "payload": {
                    "$ref": "#/components/schemas/test_2/Message/Response/Payload"
                },
            },
        },
        "schemas": {
            "test_1/TestTopic/Message/Msg/Payload": {
                "title": "test_1/TestTopic/Message/Msg/Payload",
                "type": "string",
            },
            "test_2/Message/Response/Payload": {
                "title": "test_2/Message/Response/Payload",
                "type": "string",
            },
        },
        "securitySchemes": {},
    },
}


def test_base_security_schema():
    ssl_context = ssl.create_default_context()
    security = BaseSecurity(ssl_context=ssl_context)

    broker = KafkaBroker("localhost:9092", security=security)
    app = FastStream(broker)

    @broker.publisher("test_2")
    @broker.subscriber("test_1")
    async def test_topic(msg: str) -> str:
        pass

    schema = get_app_schema(app).to_jsonable()
    print(schema)
    assert schema == basic_schema


def test_plaintext_security_schema():
    ssl_context = ssl.create_default_context()
    security = SASLPlaintext(
        ssl_context=ssl_context,
        username="admin",
        password="password",  # pragma: allowlist secret
    )

    broker = KafkaBroker("localhost:9092", security=security)
    app = FastStream(broker)

    @broker.publisher("test_2")
    @broker.subscriber("test_1")
    async def test_topic(msg: str) -> str:
        pass

    schema = get_app_schema(app).to_jsonable()

    plaintext_security_schema = deepcopy(basic_schema)
    plaintext_security_schema["servers"]["development"]["security"] = [
        {"user-password": []}
    ]
    plaintext_security_schema["components"]["securitySchemes"] = {
        "user-password": {"type": "userPassword"}
    }

    assert schema == plaintext_security_schema


def test_scram256_security_schema():
    ssl_context = ssl.create_default_context()
    security = SASLScram256(
        ssl_context=ssl_context,
        username="admin",
        password="password",  # pragma: allowlist secret
    )

    broker = KafkaBroker("localhost:9092", security=security)
    app = FastStream(broker)

    @broker.publisher("test_2")
    @broker.subscriber("test_1")
    async def test_topic(msg: str) -> str:
        pass

    schema = get_app_schema(app).to_jsonable()

    sasl256_security_schema = deepcopy(basic_schema)
    sasl256_security_schema["servers"]["development"]["security"] = [{"scram256": []}]
    sasl256_security_schema["components"]["securitySchemes"] = {
        "scram256": {"type": "scramSha256"}
    }

    assert schema == sasl256_security_schema


def test_scram512_security_schema():
    ssl_context = ssl.create_default_context()
    security = SASLScram512(
        ssl_context=ssl_context,
        username="admin",
        password="password",  # pragma: allowlist secret
    )

    broker = KafkaBroker("localhost:9092", security=security)
    app = FastStream(broker)

    @broker.publisher("test_2")
    @broker.subscriber("test_1")
    async def test_topic(msg: str) -> str:
        pass

    schema = get_app_schema(app).to_jsonable()

    sasl512_security_schema = deepcopy(basic_schema)
    sasl512_security_schema["servers"]["development"]["security"] = [{"scram512": []}]
    sasl512_security_schema["components"]["securitySchemes"] = {
        "scram512": {"type": "scramSha512"}
    }

    assert schema == sasl512_security_schema
