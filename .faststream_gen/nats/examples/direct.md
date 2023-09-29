# Direct

The **Direct** Subject is the basic way to route messages in *NATS*. Its essence is very simple:
a `subject` sends messages to all consumers subscribed to it.

## Scaling

If one `subject` is being listened to by several consumers with the same `queue group`, the message will go to a random consumer each time.

Thus, *NATS* can independently balance the load on queue consumers. You can increase the processing speed of the message flow from the queue by simply launching additional instances of the consumer service. You don't need to make changes to the current infrastructure configuration: *NATS* will take care of how to distribute messages between your services.

## Example

The **Direct** Subject is the type used in **FastStream** by default: you can simply declare it as follows

```python
@broker.handler("test_subject")
async def handler():
...
```

Full example:

```python linenums="1"
from faststream import FastStream, Logger
from faststream.nats import NatsBroker

broker = NatsBroker()
app = FastStream(broker)

@broker.subscriber("test-subj-1", "workers")
async def base_handler1(logger: Logger):
    logger.info("base_handler1")

@broker.subscriber("test-subj-1", "workers")
async def base_handler2(logger: Logger):
    logger.info("base_handler2")

@broker.subscriber("test-subj-2", "workers")
async def base_handler3(logger: Logger):
    logger.info("base_handler3")

@app.after_startup
async def send_messages():
    await broker.publish("", "test-subj-1")  # handlers: 1 or 2
    await broker.publish("", "test-subj-1")  # handlers: 1 or 2
    await broker.publish("", "test-subj-2")  # handlers: 3
```

### Consumer Announcement

To begin with, we have declared several consumers for two `subjects`: `test-subj-1` and `test-subj-2`:

```python linenums="7" hl_lines="1 5 9"
@broker.subscriber("test-subj-1", "workers")
async def base_handler1(logger: Logger):
    logger.info("base_handler1")

@broker.subscriber("test-subj-1", "workers")
async def base_handler2(logger: Logger):
    logger.info("base_handler2")

@broker.subscriber("test-subj-2", "workers")
async def base_handler3(logger: Logger):
    logger.info("base_handler3")
```

!!! note
    Note that all consumers are subscribed using the same `queue_group`. Within the same service, this does not make sense, since messages will come to these handlers in turn.
    Here, we emulate the work of several consumers and load balancing between them.

### Message Distribution

Now the distribution of messages between these consumers will look like this:

```python
    await broker.publish("", "test-subj-1")  # handlers: 1 or 2
```

The message `1` will be sent to `handler1` or `handler2` because they are listening to one `subject` within one `queue group`.

---

```python
    await broker.publish("", "test-subj-1")  # handlers: 1 or 2
```

Message `2` will be sent similarly to message `1`.

---

```python
    await broker.publish("", "test-subj-2")  # handlers: 3
```

The message `3` will be sent to `handler3` because it is the only one listening to `test-subj-2`.
