from typing import Any

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from faststream.asgi import AsgiFastStream, AsgiResponse, get, make_ping_asgi


class AsgiTestcase:
    def get_broker(self, **kwargs) -> Any:
        raise NotImplementedError

    def get_test_broker(self, broker) -> Any:
        raise NotImplementedError

    def test_not_found(self):
        app = AsgiFastStream()

        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 404

    def test_ws_not_found(self):
        app = AsgiFastStream()

        with TestClient(app) as client:  # noqa: SIM117
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect("/ws"):  # raises error
                    pass

    def test_asgi_ping_unhealthy(self):
        broker = self.get_broker()

        app = AsgiFastStream(
            asgi_routes=[
                ("/health", make_ping_asgi(broker, timeout=5.0)),
            ],
        )

        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_asgi_ping_healthy(self):
        broker = self.get_broker()

        app = AsgiFastStream(
            broker,
            asgi_routes=[("/health", make_ping_asgi(broker, timeout=5.0))],
        )

        async with self.get_test_broker(broker):
            with TestClient(app) as client:
                response = client.get("/health")
                assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_asyncapi_asgi(self):
        broker = self.get_broker()

        app = AsgiFastStream(broker, asyncapi_path="/docs")

        async with self.get_test_broker(broker):
            with TestClient(app) as client:
                response = client.get("/docs")
                assert response.status_code == 200
                assert response.text

    def test_get_decorator(self):
        @get
        async def some_handler(scope):
            return AsgiResponse(body=b"test", status_code=200)

        app = AsgiFastStream(asgi_routes=[("/test", some_handler)])

        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 200
            assert response.text == "test"
