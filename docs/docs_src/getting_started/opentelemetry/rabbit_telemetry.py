from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from faststream.rabbit.opentelemetry import RabbitTelemetryMiddleware

resource = Resource.create(attributes={"service.name": "faststream"})
tracer_provider = TracerProvider(resource=resource)

broker = RabbitBroker(middlewares=(RabbitTelemetryMiddleware(tracer_provider=tracer_provider),))
app = FastStream(broker)
