from importlib import import_module
from unittest.mock import Mock, call, patch


class BaseTestCase:
    middleware_cls_path: str
    broker_cls_path: str
    doc_path: str
    app_cls_path = "faststream.FastStream"

    def test_prometheus_getting_started(self):
        fake_middleware = Mock()
        fake_middleware_cls = Mock(return_value=fake_middleware)
        fake_broker_cls = Mock()
        fake_app_cls = Mock()
        with (
            patch(
                self.middleware_cls_path,
                new=fake_middleware_cls,
            ),
            patch(self.broker_cls_path, new=fake_broker_cls),
            patch(self.app_cls_path, new=fake_app_cls),
        ):
            doc = import_module(self.doc_path)

            assert fake_middleware_cls.mock_calls == [call(registry=doc.registry)]
            assert fake_broker_cls.mock_calls == [call(middlewares=(fake_middleware,))]
            assert fake_app_cls.mock_calls == [call(doc.broker)]


class BaseAsgiTestCase(BaseTestCase):
    app_cls_path = "faststream.asgi.AsgiFastStream"

    def test_prometheus_getting_started(self):
        fake_middleware = Mock()
        fake_middleware_cls = Mock(return_value=fake_middleware)
        fake_broker_cls = Mock()
        fake_app_cls = Mock()
        fake_prom_asgi_app = Mock()
        fake_make_asgi_app = Mock(return_value=fake_prom_asgi_app)
        with (
            patch(
                self.middleware_cls_path,
                new=fake_middleware_cls,
            ),
            patch(self.broker_cls_path, new=fake_broker_cls),
            patch("faststream.asgi.AsgiFastStream", new=fake_app_cls),
            patch("prometheus_client.make_asgi_app", new=fake_make_asgi_app),
        ):
            doc = import_module(self.doc_path)

            assert fake_middleware_cls.mock_calls == [call(registry=doc.registry)]
            assert fake_broker_cls.mock_calls == [call(middlewares=(fake_middleware,))]
            assert fake_make_asgi_app.mock_calls == [call(doc.registry)]
            assert fake_app_cls.mock_calls == [
                call(
                    doc.broker,
                    asgi_routes=[
                        ("/metrics", fake_prom_asgi_app),
                    ],
                )
            ]
