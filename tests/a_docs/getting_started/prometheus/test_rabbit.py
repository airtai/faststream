from .base import BaseTestCase


class TestCaseRabbit(BaseTestCase):
    middleware_cls_path = "faststream.rabbit.prometheus.RabbitPrometheusMiddleware"
    broker_cls_path = "faststream.rabbit.RabbitBroker"
    doc_path = "docs.docs_src.getting_started.prometheus.rabbit"
