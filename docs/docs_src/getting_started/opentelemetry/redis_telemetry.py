from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from faststream import FastStream
from faststream.redis import RedisBroker
from faststream.redis.opentelemetry import RedisTelemetryMiddleware

resource = Resource.create(attributes={"service.name": "faststream"})
tracer_provider = TracerProvider(resource=resource)

broker = RedisBroker(middlewares=(RedisTelemetryMiddleware(tracer_provider=tracer_provider),))
app = FastStream(broker)
