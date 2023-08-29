from typing import Any, Callable, Type

from fastapi import FastAPI
from fastapi.testclient import TestClient
from loguru import logger

from faststream.asyncapi.generate import get_app_schema
from faststream.broker.core.abc import BrokerUsecase
from faststream.broker.fastapi.router import StreamRouter
from faststream.broker.types import MsgType


class FastAPITestCase:
    broker_class: Type[StreamRouter[MsgType]]
    broker_wrapper: Callable[[BrokerUsecase[MsgType, Any]], BrokerUsecase[MsgType, Any]]

    def test_fastapi_asyncapi_routes(self):
        broker = self.broker_class(schema_url="/asyncapi_schema")
        logger.debug(broker)
        broker.broker = self.broker_wrapper(broker.broker)

        @broker.subscriber("test")
        async def handler():
            ...

        app = FastAPI(lifespan=broker.lifespan_context)
        app.include_router(broker)

        logger.debug(broker)
        schema = get_app_schema(broker)

        with TestClient(app) as client:
            response_json = client.get("/asyncapi_schema.json")
            assert response_json.json() == schema.to_jsonable()

            response_yaml = client.get("/asyncapi_schema.yaml")
            assert response_yaml.text == schema.to_yaml()

            response_html = client.get("/asyncapi_schema")
            assert response_html.status_code == 200

    def test_fastapi_asyncapi_not_fount(self):
        broker = self.broker_class(include_in_schema=False)
        broker.broker = self.broker_wrapper(broker.broker)
        app = FastAPI(lifespan=broker.lifespan_context)
        app.include_router(broker)

        with TestClient(app) as client:
            response_json = client.get("/asyncapi.json")
            assert response_json.status_code == 404

            response_yaml = client.get("/asyncapi.yaml")
            assert response_yaml.status_code == 404

            response_html = client.get("/asyncapi")
            assert response_html.status_code == 404

    def test_fastapi_asyncapi_not_fount_by_url(self):
        broker = self.broker_class(schema_url=None)
        broker.broker = self.broker_wrapper(broker.broker)
        app = FastAPI(lifespan=broker.lifespan_context)
        app.include_router(broker)

        with TestClient(app) as client:
            response_json = client.get("/asyncapi.json")
            assert response_json.status_code == 404

            response_yaml = client.get("/asyncapi.yaml")
            assert response_yaml.status_code == 404

            response_html = client.get("/asyncapi")
            assert response_html.status_code == 404
