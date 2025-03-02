from typing import Any
from unittest.mock import AsyncMock

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from faststream.asgi import (
    AsgiFastStream,
    AsgiResponse,
    get,
    make_asyncapi_asgi,
    make_ping_asgi,
)
from faststream.specification import AsyncAPI


class AsgiTestcase:
    def get_broker(self, **kwargs) -> Any:
        raise NotImplementedError

    def get_test_broker(self, broker) -> Any:
        raise NotImplementedError

<<<<<<< HEAD
    def test_not_found(self) -> None:
        app = AsgiFastStream(AsyncMock())
=======
    @pytest.mark.asyncio
    async def test_not_found(self):
        broker = self.get_broker()
        app = AsgiFastStream(broker)
>>>>>>> 60c04eb6d5ecdeef8d958c197adaf2ffef193e2b

        async with self.get_test_broker(broker):
            with TestClient(app) as client:
                response = client.get("/")
                assert response.status_code == 404

<<<<<<< HEAD
    def test_ws_not_found(self) -> None:
        app = AsgiFastStream(AsyncMock())
=======
    @pytest.mark.asyncio
    async def test_ws_not_found(self):
        broker = self.get_broker()
>>>>>>> 60c04eb6d5ecdeef8d958c197adaf2ffef193e2b

        app = AsgiFastStream(broker)

<<<<<<< HEAD
    def test_asgi_ping_unhealthy(self) -> None:
        broker = self.get_broker()

        app = AsgiFastStream(
            AsyncMock(),
=======
        async with self.get_test_broker(broker):
            with TestClient(app) as client:
                with pytest.raises(WebSocketDisconnect):
                    with client.websocket_connect("/ws"):  # raises error
                        pass

    @pytest.mark.asyncio
    async def test_asgi_ping_unhealthy(self):
        broker = self.get_broker()

        app = AsgiFastStream(
            broker,
>>>>>>> 60c04eb6d5ecdeef8d958c197adaf2ffef193e2b
            asgi_routes=[
                ("/health", make_ping_asgi(broker, timeout=5.0)),
            ],
        )
        async with self.get_test_broker(broker) as br:
            br.ping = AsyncMock()
            br.ping.return_value = False

<<<<<<< HEAD
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 500, response.status_code
=======
            with TestClient(app) as client:
                response = client.get("/health")
                assert response.status_code == 500
>>>>>>> 60c04eb6d5ecdeef8d958c197adaf2ffef193e2b

    @pytest.mark.asyncio()
    async def test_asgi_ping_healthy(self) -> None:
        broker = self.get_broker()

        app = AsgiFastStream(
            broker,
            asgi_routes=[("/health", make_ping_asgi(broker, timeout=5.0))],
        )

        async with self.get_test_broker(broker):
            with TestClient(app) as client:
                response = client.get("/health")
                assert response.status_code == 204

    @pytest.mark.asyncio()
    async def test_asyncapi_asgi(self) -> None:
        broker = self.get_broker()

        app = AsgiFastStream(
            broker,
            asgi_routes=[("/docs", make_asyncapi_asgi(AsyncAPI(broker)))],
        )

        async with self.get_test_broker(broker):
            with TestClient(app) as client:
                response = client.get("/docs")
                assert response.status_code == 200
                assert response.text

<<<<<<< HEAD
    def test_get_decorator(self) -> None:
=======
    @pytest.mark.asyncio
    async def test_get_decorator(self):
>>>>>>> 60c04eb6d5ecdeef8d958c197adaf2ffef193e2b
        @get
        async def some_handler(scope) -> AsgiResponse:
            return AsgiResponse(body=b"test", status_code=200)

<<<<<<< HEAD
        app = AsgiFastStream(AsyncMock(), asgi_routes=[("/test", some_handler)])
=======
        broker = self.get_broker()
        app = AsgiFastStream(broker, asgi_routes=[("/test", some_handler)])
>>>>>>> 60c04eb6d5ecdeef8d958c197adaf2ffef193e2b

        async with self.get_test_broker(broker):
            with TestClient(app) as client:
                response = client.get("/test")
                assert response.status_code == 200
                assert response.text == "test"
