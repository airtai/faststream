# Topic Exchange

**Topic** Exchange is a powerful *RabbitMQ* routing tool. This type of `exchange` sends messages to the queue in accordance with the *pattern* specified when they are connected to `exchange` and the `routing_key` of the message itself.

At the same time, if the queue listens to several consumers, messages will also be distributed among them.

## Example

```python linenums="1"
from faststream import FastStream, Logger
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue

broker = RabbitBroker()
app = FastStream(broker)

exch = RabbitExchange("exchange", auto_delete=True, type=ExchangeType.TOPIC)

queue_1 = RabbitQueue("test-queue-1", auto_delete=True, routing_key="*.info")
queue_2 = RabbitQueue("test-queue-2", auto_delete=True, routing_key="*.debug")


@broker.subscriber(queue_1, exch)
async def base_handler1(logger: Logger):
    logger.info("base_handler1")


@broker.subscriber(queue_1, exch)
async def base_handler2(logger: Logger):
    logger.info("base_handler2")


@broker.subscriber(queue_2, exch)
async def base_handler3(logger: Logger):
    logger.info("base_handler3")


@app.after_startup
async def send_messages():
    await broker.publish(routing_key="logs.info", exchange=exch)  # handlers: 1
    await broker.publish(routing_key="logs.info", exchange=exch)  # handlers: 2
    await broker.publish(routing_key="logs.info", exchange=exch)  # handlers: 1
    await broker.publish(routing_key="logs.debug", exchange=exch)  # handlers: 3
```

### Consumer Announcement

To begin with, we announced our **Topic** exchange and several queues that will listen to it:

```python linenums="7" hl_lines="1 3-4"
exch = RabbitExchange("exchange", auto_delete=True, type=ExchangeType.TOPIC)

queue_1 = RabbitQueue("test-queue-1", auto_delete=True, routing_key="*.info")
queue_2 = RabbitQueue("test-queue-2", auto_delete=True, routing_key="*.debug")
```

At the same time, in the `routing_key` of our queues, we specify the *pattern* of routing keys that will be processed by this queue.

Then we signed up several consumers using the advertised queues to the `exchange` we created

```python linenums="12" hl_lines="1 5 9"

@broker.subscriber(queue_1, exch)
async def base_handler1(logger: Logger):
    logger.info("base_handler1")


@broker.subscriber(queue_1, exch)
async def base_handler2(logger: Logger):
    logger.info("base_handler2")


```

!!! note
    `handler1` and `handler2` are subscribed to the same `exchange` using the same queue:
    within a single service, this does not make a sense, since messages will come to these handlers in turn.
    Here we emulate the work of several consumers and load balancing between them.

### Message distribution

Now the distribution of messages between these consumers will look like this:

```python linenums="26"

```

Message `1` will be sent to `handler1` because it listens to `exchange` using a queue with the routing key `*.info`

---

```python linenums="27"

```

Message `2` will be sent to `handler2` because it listens to `exchange` using the same queue, but `handler1` is busy

---

```python linenums="28"
@app.after_startup
```

Message `3` will be sent to `handler1` again, because it is currently free

---

```python linenums="29"
async def send_messages():
```

Message `4` will be sent to `handler3`, because it is the only one listening to `exchange` using a queue with the routing key `*.debug`