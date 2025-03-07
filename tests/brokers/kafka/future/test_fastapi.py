from faststream.kafka.fastapi import KafkaRouter as StreamRouter
from faststream.kafka.router import KafkaRouter
from tests.brokers.base.future import FastapiTestCase


class TestRouter(FastapiTestCase):
    router_class = StreamRouter
    broker_router_class = KafkaRouter
