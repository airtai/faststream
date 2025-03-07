from faststream.confluent.fastapi import KafkaRouter as StreamRouter
from faststream.confluent.router import KafkaRouter
from tests.brokers.base.future import FastapiTestCase


class TestRouter(FastapiTestCase):
    router_class = StreamRouter
    broker_router_class = KafkaRouter
