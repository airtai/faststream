---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# ASGI support

Often you need to not just run your application to consume messages, but make it the real part of your services ecosystem: with *Prometheus metrics*, K8S *leviness* and *readiness probes*, *traces* and other observability staff.

Unfortunately, such functional can't be implemented by broker-features only and you have to provide several **HTTP** endpoints in your app.

For sure, you can use **FastStream** as a part of your any **ASGI** frameworks ([integrations](./integrations/frameworks/index.md){.internal-link}), but the fewer dependencies, the better, right?

## AsgiFastStream

Helpfully, we have built-in **ASGI** support. It is very limited, but good enough to provides you with basic functional for metrics and healthcheks endpoints implementation.

Let's take a look at the following example:

```python linenums="1" hl_lines="2 5" title="main.py"
from faststream.nats import NatsBroker
from faststream.asgi import AsgiFastStream

broker = NatsBroker()
app = AsgiFastStream(broker)
```

This simple example just provides you with an ability to run the app using regular **ASGI** servers:

```shell
uvicorn main:app
```

Now it does nothing but launches the app itself as a **ASGI lifespan**.


### ASGI routes

It doesn't look really helpful, so let's add some **HTTP** endpoints.

At first, we have already written wrapper on top of broker to make ready-to-use **ASGI** healthcheck endpoint for you

```python linenums="1" hl_lines="2 9"
from faststream.nats import NatsBroker
from faststream.asgi import AsgiFastStream, make_ping_asgi

broker = NatsBroker()

app = AsgiFastStream(
    broker,
    asgi_routes=[
        ("/health", make_ping_asgi(broker, timeout=5.0)),
    ]
)
```

!!! note
    This `/health` endpoint calls `#!python broker.ping()` method and return **HTTP 204** or **HTTP 500** statuses.
  
### Custom ASGI routes

**AsgiFastStream** is able to call any **ASGI**-compatible callable objects, so you can use any endpoints from other libraries if they are compatible with the protocol.

But, if you need to write you own simple **HTTP**-endpoint you can use our `#!python @get` decorator as in the following example:

```python linenums="1" hl_lines="2 6-8 12"
from faststream.nats import NatsBroker
from faststream.asgi import AsgiFastStream, AsgiResponse, get

broker = NatsBroker()

@get
async def liveness_ping(scope):
    return AsgiResponse(b"", status_code=200)

app = AsgiFastStream(
    broker,
    asgi_routes=[("/health", liveness_ping)]
)
```

Or you can write **ASGI** endpoint by yourself

```python
async def liveness_ping(scope, receive, send):
    return AsgiResponse(b"", status_code=200)
```

!!! tip
    You need no to setup all routes by `asgi_routes=[]` initial option.<br/>
    You can use `#!python app.mount("/healh", asgi_endpoint)` method instead.

### AsyncAPI documentation

Also, you can host your **AsyncAPI** documentation without new process, run by [`#!shell faststream docs serve ...`](./asyncapi/hosting.md){.internal-link}, but in the same container and runtime.

Just create `AsgiFastStream` object with a special option:

```python linenums="1" hl_lines="8"
from faststream.nats import NatsBroker
from faststream.asgi import AsgiFastStream

broker = NatsBroker()

app = AsgiFastStream(
    broker,
    asyncapi_path="/docs",
)
```

Now, your **AsyncAPI HTML** representation can be founded in the net by `/docs` url.

## Another ASGI compatibility

Moreover, our wrappers can be used as a ready-to-use endpoins for other **ASGI** frameworks. It can be very helpful in cases, then you are running **FastStream** in the same runtime with any **ASGI** framework.

Just follow the example in such cases:

```python linenums="1" hl_lines="6 19-20"
from contextlib import asynccontextmanager

from fastapi import FastAPI
from faststream import FastStream
from faststream.nats import NatsBroker
from faststream.asgi import make_ping_asgi, make_asyncapi_asgi

broker = NatsBroker()

@asynccontextmanager
async def start_broker(app):
    """Start the broker with the app."""
    async with broker:
        await broker.start()
        yield

app = FastAPI(lifespan=start_broker)

app.mount("/health", make_ping_asgi(broker, timeout=5.0))
app.mount("/asyncapi", make_asyncapi_asgi(FastStream(broker)))
```
