# Direct Exchange

**Direct** Exchange is the basic way to route messages in *RabbitMQ*. Its core is very simple: `exchange` sends messages to those queues, `routing_key` which matches the `routing_key` of the message being sent.

!!! note
    **Default** Exchange, to which all queues in *RabbitMQ* are subscribed, has the **Direct** type by default

## Scaling

If several consumers are listening to the same queue, messages will go to the one of them (round-robin). This behavior is common for all types of `exchange`, because it refers to the queue itself. The type of `exchange` affects which queues the message gets into.

Thus, *RabbitMQ* can independently balance the load on queue consumers. You can increase the processing speed
of the message flow from the queue by launching additional instances of a consumer service. You don't need to make changes to the current infrastructure configuration: *RabbitMQ* will take care of how to distribute messages between your services.

## Example

!!! tip
    **Direct** Exchange is the type used in **FastStream** by default: you can simply declare it as follows

    ```python
    @broker.subscriber("test_queue", "test_exchange")
    async def handler():
        ...
    ```

The argument `auto_delete=True` in this and subsequent examples is used only to clear the state of *RabbitMQ* after example runs

```python linenums="1"
from faststream import FastStream, Logger
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

broker = RabbitBroker()
app = FastStream(broker)

exch = RabbitExchange("exchange", auto_delete=True)

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
    await broker.publish(queue="test-q-1", exchange=exch)  # handlers: 1
    await broker.publish(queue="test-q-1", exchange=exch)  # handlers: 2
    await broker.publish(queue="test-q-1", exchange=exch)  # handlers: 1
    await broker.publish(queue="test-q-2", exchange=exch)  # handlers: 3
```

### Consumer Announcement

To begin with, we announced our **Direct** exchange and several queues that will listen to it:

```python linenums="7"
exch = RabbitExchange("exchange", auto_delete=True)

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
    await broker.publish(queue="test-q-1", exchange=exch)  # handlers: 1
```

Message `1` will be sent to `handler1` because it listens to `exchange` using a queue with the routing key `test-q-1`

---

```python linenums="31"
    await broker.publish(queue="test-q-1", exchange=exch)  # handlers: 2
```

Message `2` will be sent to `handler2` because it listens to `exchange` using the same queue, but `handler1` is busy

---

```python linenums="32"
    await broker.publish(queue="test-q-1", exchange=exch)  # handlers: 1
```

Message `3` will be sent to `handler1` again, because it is currently free

---

```python linenums="33"
    await broker.publish(queue="test-q-2", exchange=exch)  # handlers: 3
```

Message `4` will be sent to `handler3`, because it is the only one listening to `exchange` using a queue with the routing key `test-q-2`
