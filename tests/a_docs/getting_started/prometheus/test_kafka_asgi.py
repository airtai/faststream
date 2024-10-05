from .base import BaseAsgiTestCase
from .test_kafka import TestCaseKafka


class TestCaseAsgiKafka(BaseAsgiTestCase, TestCaseKafka):
    doc_path = "docs.docs_src.getting_started.prometheus.kafka_asgi"
