from .base import BaseTestCase


class TestCaseKafka(BaseTestCase):
    middleware_cls_path = "faststream.kafka.prometheus.KafkaPrometheusMiddleware"
    broker_cls_path = "faststream.kafka.KafkaBroker"
    doc_path = "docs.docs_src.getting_started.prometheus.kafka"
