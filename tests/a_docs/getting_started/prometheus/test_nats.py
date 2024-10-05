from .base import BaseTestCase


class TestCaseNats(BaseTestCase):
    middleware_cls_path = "faststream.nats.prometheus.NatsPrometheusMiddleware"
    broker_cls_path = "faststream.nats.NatsBroker"
    doc_path = "docs.docs_src.getting_started.prometheus.nats"
