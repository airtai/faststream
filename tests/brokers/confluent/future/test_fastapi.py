import pytest

from faststream.confluent.fastapi import KafkaRouter as StreamRouter
from faststream.confluent.router import KafkaRouter
from tests.brokers.base.future.fastapi import FastapiTestCase


@pytest.mark.confluent
class TestRouter(FastapiTestCase):
    router_class = StreamRouter
    broker_router_class = KafkaRouter
