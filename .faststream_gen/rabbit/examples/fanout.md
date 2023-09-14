# Fanout Exchange

**Fanout** Exchange is an even simpler, but slightly less popular way of routing in *RabbitMQ*. This type of `exchange` sends messages
to all queues subscribed to it, ignoring any arguments of the message.

At the same time, if the queue listens to several consumers, messages will also be distributed among them.

## Example

```python linenums="1"
from faststream import FastStream, Logger
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue

broker = RabbitBroker()
app = FastStream(broker)

exch = RabbitExchange("exchange", auto_delete=True, type=ExchangeType.FANOUT)

queue_1 = RabbitQueue("test-q-1", auto_delete=True)
queue_2 = RabbitQueue("test-q-2", auto_delete=True)


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
    await broker.publish(exchange=exch)  # handlers: 1, 3
    await broker.publish(exchange=exch)  # handlers: 2, 3
    await broker.publish(exchange=exch)  # handlers: 1, 3
    await broker.publish(exchange=exch)  # handlers: 2, 3
```

### Consumer Announcement

To begin with, we announced our **Fanout** exchange and several queues that will listen to it:

```python linenums="7" hl_lines="1"
exch = RabbitExchange("exchange", auto_delete=True, type=ExchangeType.FANOUT)

queue_1 = RabbitQueue("test-q-1", auto_delete=True)
queue_2 = RabbitQueue("test-q-2", auto_delete=True)
```

Then we signed up several consumers using the advertised queues to the `exchange` we created

```python linenums="13" hl_lines="1 6 11"
@broker.subscriber(queue_1, exch)
async def base_handler1(logger: Logger):
    logger.info("base_handler1")


@broker.subscriber(queue_1, exch)
async def base_handler2(logger: Logger):
    logger.info("base_handler2")


@broker.subscriber(queue_2, exch)
async def base_handler3(logger: Logger):
    logger.info("base_handler3")
```

!!! note
    `handler1` and `handler2` are subscribed to the same `exchange` using the same queue:
    within a single service, this does not make a sense, since messages will come to these handlers in turn.
    Here we emulate the work of several consumers and load balancing between them.

### Message distribution

Now the distribution of messages between these consumers will look like this:

```python linenums="30"
    await broker.publish(exchange=exch)  # handlers: 1, 3
```

Message `1` will be sent to `handler1` and `handler3`, because they listen to `exchange` using different queues

---

```python linenums="31"
    await broker.publish(exchange=exch)  # handlers: 2, 3
```

Message `2` will be sent to `handler2` and `handler3`, because `handler2` listens to `exchange` using the same queue as `handler1`

---

```python linenums="32"
    await broker.publish(exchange=exch)  # handlers: 1, 3
```

Message `3` will be sent to `handler1` and `handler3`

---

```python linenums="33"
    await broker.publish(exchange=exch)  # handlers: 2, 3
```

Message `4` will be sent to `handler3` and `handler3`

---

!!! note
    When sending messages to **Fanout** exchange, it makes no sense to specify the arguments `queue` or `routing_key`, because they will be ignored
