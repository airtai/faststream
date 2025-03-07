from faststream.rabbit.fastapi import RabbitRouter as StreamRouter
from faststream.rabbit.router import RabbitRouter
from tests.brokers.base.future import FastapiTestCase


class TestRouter(FastapiTestCase):
    router_class = StreamRouter
    broker_router_class = RabbitRouter
