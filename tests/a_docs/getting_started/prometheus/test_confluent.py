from .base import BaseTestCase


class TestCaseConfluent(BaseTestCase):
    middleware_cls_path = "faststream.confluent.prometheus.KafkaPrometheusMiddleware"
    broker_cls_path = "faststream.confluent.KafkaBroker"
    doc_path = "docs.docs_src.getting_started.prometheus.confluent"
