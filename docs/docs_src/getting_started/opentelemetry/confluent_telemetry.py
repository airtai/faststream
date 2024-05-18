from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from faststream import FastStream
from faststream.confluent import KafkaBroker
from faststream.confluent.opentelemetry import KafkaTelemetryMiddleware

resource = Resource.create(attributes={"service.name": "faststream"})
tracer_provider = TracerProvider(resource=resource)

broker = KafkaBroker(middlewares=(KafkaTelemetryMiddleware(tracer_provider=tracer_provider),))
app = FastStream(broker)
