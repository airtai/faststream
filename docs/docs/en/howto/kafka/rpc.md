---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Kafka RPC requests

Unfortunatelly, **Kafka** has no built-in **RPC** mechanism or zero-cost topics, but you can emulate such behavior using messaging pattern.

To implement it you should create persistent topic to consume responses stream and match them with requests by correlation id.

It can be easely implemented with **FastStream**, so let's take a look at the code. At first, we will try to write simple **FastStream**-featured implementation and then create reusable tool based on it.

## Raw implementation

Let's image, that we have simple **FastStream** echo subscriber like this:

```python linenums="1" hl_lines="7-9"
from faststream import FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker()
app = FastStream(broker)

@broker.subscriber("echo-topic")
async def echo_handler(msg: Any) -> Any:
    return msg
```

It does nothing, but publishes responses to all messages with `reply_to` header.

Now, we want to send a message and consume echo callback. This reason we should create some *reply consumer* in our producer service. It can looks like the followed:

```python linenums="1" hl_lines="13-16 18-19"
from asyncio import Future
from typing import Annotated

from faststream import FastStream, Context
from faststream.kafka import KafkaBroker, KafkaMessage

broker = KafkaBroker()
app = FastStream(broker)

@broker.subscriber("responses")
async def response_handler(
    msg: KafkaMessage,
    responses: Annotated[
        dict[str, Future[bytes]],
        Context("responses", initial=dict),
    ],
) -> None:
    if (future := responses.pop(msg.correlation_id, None)):
        future.set_result(msg.body)
```

This handler just maps incoming messages to their requests by `correlation_id` field.

Then we should just publish a message with `#!python reply_to="responses"` header, create a Future object and wait for it.

```python linenums="1" hl_lines="8-9 13-14 17-18"
@app.after_startup
async def send_request(
    responses: Annotated[
        dict[str, Future[bytes]],
        Context("responses", initial=dict),
    ],
) -> None:
    correlation_id = str(uuid4())
    future = responses[correlation_id] = Future[bytes]()

    await broker.publish(
        "echo", "echo-topic",
        reply_to="responses",
        correlation_id=correlation_id,
    )

    data: bytes = await future
    assert data == b"echo"  # returned from echo
```

!!! note
    `message.correlation_id` and `message.reply_to` are **FastStream**-specific message headers, but you can set them by any **Kafka** client you are using.

??? example "Full Example"
    ```python linenums="1"
    from asyncio import Future, wait_for
    from typing import Annotated, Any
    from uuid import uuid4

    from faststream import FastStream, Context
    from faststream.kafka import KafkaBroker, KafkaMessage

    broker = KafkaBroker()
    app = FastStream(broker)

    @broker.subscriber("echo-topic")
    async def echo_handler(msg: Any) -> Any:
        return msg

    @broker.subscriber("responses")
    async def response_handler(
        msg: KafkaMessage,
        responses: Annotated[
            dict[str, Future[bytes]],
            Context("responses", initial=dict),
        ],
    ) -> None:
        if (future := responses.pop(msg.correlation_id, None)):
            future.set_result(msg.body)

    @app.after_startup
    async def send_request(
        responses: Annotated[
            dict[str, Future[bytes]],
            Context("responses", initial=dict),
        ],
    ) -> None:
        correlation_id = str(uuid4())
        future = responses[correlation_id] = Future[bytes]()

        await broker.publish("echo", "echo-topic", reply_to="responses", correlation_id=correlation_id)

        try:
            data: bytes = await wait_for(future, timeout=10.0)
        except TimeoutError:
            responses.pop(correlation_id, None)
            raise
        
        assert data == b"echo"
    ```

## Reusable class

Now, when we have already working **Kafka RPC** implementation, we can incapsulate it to reusable class, that can copy-pasted between services.

```python linenums="1"
from uuid import uuid4
from asyncio import Future, wait_for

from faststream.types import SendableMessage
from faststream.kafka import KafkaMessage

class RPCWorker:
    def __init__(self, broker: KafkaBroker, reply_topic: str) -> None:
        self.responses: dict[str, Future[bytes]] = {}
        self.broker = broker
        self.reply_topic = reply_topic

        self.subscriber = broker.subscriber(reply_topic)
        self.subscriber(self._handle_responses)

    def _handle_responses(self, msg: KafkaMessage) -> None:
        """Our replies subsriber."""
        if (future := self.responses.pop(msg.correlation_id, None)):
            future.set_result(msg.body)
        
    async def request(
        self,
        data: SendableMessage,
        topic: str,
        timeout: float = 10.0,
    ) -> bytes:
        correlation_id = str(uuid4())
        future = self.responses[correlation_id] = Future[bytes]()

        await broker.publish(
            data, topic,
            reply_to=self.reply_topic,
            correlation_id=correlation_id,
        )

        try:
            response: bytes = await wait_for(future, timeout=timeout)
        except TimeoutError:
            self.responses.pop(correlation_id, None)
            raise
        else:
            return response
```

Now it can be used by the following way:

```python linenums="1" hl_lines="5 10-11"
from faststream import FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker()
worker = RPCWorker(broker, reply_topic="responses")
app = FastStream(broker)

@app.after_startup
async def send_request() -> None:
    data = await worker.request("echo", "echo-topic")
    assert data == "echo"
```

Or, if you want to make `RPCWorker` working after startup, you should add manual `start` method to it

```python
class RPCWorker:
    async def start(self) -> None:
        self.broker.setup_subscriber(self.subscriber)
        await self.subscriber.start()
```

Now it can be used after application was started

```python linenums="1" hl_lines="9-10"
from faststream import FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker()
app = FastStream(broker)

@app.after_startup
async def send_request() -> None:
    worker = RPCWorker(broker, reply_topic="responses")
    await worker.start()

    data = await worker.request("echo", "echo-topic")
    assert data == "echo"
```

??? example "Full Class Example"
    ```python linenums="1"
    from uuid import uuid4
    from asyncio import Future, wait_for

    from faststream.types import SendableMessage
    from faststream.kafka import KafkaMessage

    class RPCWorker:
        responses: dict[str, Future[bytes]]

        def __init__(self, broker: KafkaBroker, reply_topic: str) -> None:
            self.responses = {}
            self.broker = broker
            self.reply_topic = reply_topic

            self.subscriber = broker.subscriber(reply_topic)
            self.subscriber(self._handle_responses)
        
        async def start(self) -> None:
            self.broker.setup_subscriber(self.subscriber)
            await self.subscriber.start()
        
        async def stop(self) -> None:
            await self.subscriber.close()

        def _handle_responses(self, msg: KafkaMessage) -> None:
            if (future := self.responses.pop(msg.correlation_id, None)):
                future.set_result(msg.body)
            
        async def request(
            self,
            data: SendableMessage,
            topic: str,
            timeout: float = 10.0,
        ) -> bytes:
            correlation_id = str(uuid4())
            future = self.responses[correlation_id] = Future[bytes]()

            await broker.publish(
                data, topic,
                reply_to=self.reply_topic,
                correlation_id=correlation_id,
            )

            try:
                response: bytes = await wait_for(future, timeout=timeout)
            except TimeoutError:
                self.responses.pop(correlation_id, None)
                raise
            else:
                return response
    ```