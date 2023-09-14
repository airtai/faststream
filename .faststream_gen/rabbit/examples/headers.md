# Header Exchange

**Header** Exchange is the most complex and flexible way to route messages in *RabbitMQ*. This `exchange` type sends messages
to queues in according the matching of a queues binding arguments  with message headers.

At the same time, if the queue listens to several consumers, messages will also be distributed among them.

## Example

```python linenums="1"
from faststream import FastStream, Logger
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue

broker = RabbitBroker()
app = FastStream(broker)

exch = RabbitExchange("exchange", auto_delete=True, type=ExchangeType.HEADERS)

queue_1 = RabbitQueue(
    "test-queue-1",
    auto_delete=True,
    bind_arguments={"key": 1},
)
queue_2 = RabbitQueue(
    "test-queue-2",
    auto_delete=True,
    bind_arguments={"key": 2, "key2": 2, "x-match": "any"},
)
queue_3 = RabbitQueue(
    "test-queue-3",
    auto_delete=True,
    bind_arguments={"key": 2, "key2": 2, "x-match": "all"},
)


@broker.subscriber(queue_1, exch)
async def base_handler1(logger: Logger):
    logger.info("base_handler1")


@broker.subscriber(queue_1, exch)
async def base_handler2(logger: Logger):
    logger.info("base_handler2")


@broker.subscriber(queue_2, exch)
async def base_handler3(logger: Logger):
    logger.info("base_handler3")


@broker.subscriber(queue_3, exch)
async def base_handler4(logger: Logger):
    logger.info("base_handler4")


@app.after_startup
async def send_messages():
    await broker.publish(exchange=exch, headers={"key": 1})  # handlers: 1
    await broker.publish(exchange=exch, headers={"key": 1})  # handlers: 2
    await broker.publish(exchange=exch, headers={"key": 1})  # handlers: 1
    await broker.publish(exchange=exch, headers={"key": 2})  # handlers: 3
    await broker.publish(exchange=exch, headers={"key2": 2})  # handlers: 3
    await broker.publish(
        exchange=exch, headers={"key": 2, "key2": 2.0}
    )  # handlers: 3, 4
```

### Consumer Announcement

To begin with, we announced our **Fanout** exchange and several queues that will listen to it:

```python linenums="7" hl_lines="1 6 11 16"
exch = RabbitExchange("exchange", auto_delete=True, type=ExchangeType.HEADERS)

queue_1 = RabbitQueue(
    "test-queue-1",
    auto_delete=True,
    bind_arguments={"key": 1},
)
queue_2 = RabbitQueue(
    "test-queue-2",
    auto_delete=True,
    bind_arguments={"key": 2, "key2": 2, "x-match": "any"},
)
queue_3 = RabbitQueue(
    "test-queue-3",
    auto_delete=True,
    bind_arguments={"key": 2, "key2": 2, "x-match": "all"},
)
```

The `x-match` argument indicates whether the arguments should match the message headers in whole or in part.

Then we signed up several consumers using the advertised queues to the `exchange` we created

```python linenums="26" hl_lines="1 6 11 16"
@broker.subscriber(queue_1, exch)
async def base_handler1(logger: Logger):
    logger.info("base_handler1")


@broker.subscriber(queue_1, exch)
async def base_handler2(logger: Logger):
    logger.info("base_handler2")


@broker.subscriber(queue_2, exch)
async def base_handler3(logger: Logger):
    logger.info("base_handler3")


@broker.subscriber(queue_3, exch)
async def base_handler4(logger: Logger):
    logger.info("base_handler4")
```

!!! note
    `handler1` and `handler2` are subscribed to the same `exchange` using the same queue:
    within a single service, this does not make a sense, since messages will come to these handlers in turn.
    Here we emulate the work of several consumers and load balancing between them.

### Message distribution

Now the distribution of messages between these consumers will look like this:

```python linenums="48"
    await broker.publish(exchange=exch, headers={"key": 1})  # handlers: 1
```

Message `1` will be sent to `handler1`, because it listens to a queue whose `key` header matches the `key` header of the message

---

```python linenums="49"
    await broker.publish(exchange=exch, headers={"key": 1})  # handlers: 2
```

Message `2` will be sent to `handler2` because it listens to `exchange` using the same queue, but `handler1` is busy

---

```python linenums="50"
    await broker.publish(exchange=exch, headers={"key": 1})  # handlers: 1
```

Message `3` will be sent to `handler1` again, because it is currently free

---

```python linenums="51"
    await broker.publish(exchange=exch, headers={"key": 2})  # handlers: 3
```

Message `4` will be sent to `handler3`, because it listens to a queue whose `key` header coincided with the `key` header of the message

---

```python linenums="52"
    await broker.publish(exchange=exch, headers={"key2": 2})  # handlers: 3
```

Message `5` will be sent to `handler3`, because it listens to a queue whose header `key2` coincided with the header `key2` of the message

---

```python linenums="53"
    await broker.publish(
        exchange=exch, headers={"key": 2, "key2": 2.0}
    )  # handlers: 3, 4
```

Message `6` will be sent to `handler3` and `handler4`, because the message headers completely match the queue keys

---

!!! note
    When sending messages to **Header** exchange, it makes no sense to specify the arguments `queue` or `routing_key`, because they will be ignored

!!! warning
    For incredibly complex routes, you can use the option to bind an `exchange` to another `exchange`. In this case, all the same rules apply as for queues subscribed to `exchange`. The only difference is that the signed `exchange` can further distribute messages according to its own rules.

    So, for example, you can combine Topic and Header exchange types.
