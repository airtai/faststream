from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from faststream import FastStream
from faststream.nats import NatsBroker
from faststream.nats.opentelemetry import NatsTelemetryMiddleware

resource = Resource.create(attributes={"service.name": "faststream"})
tracer_provider = TracerProvider(resource=resource)

broker = NatsBroker(middlewares=(NatsTelemetryMiddleware(tracer_provider=tracer_provider),))
app = FastStream(broker)
