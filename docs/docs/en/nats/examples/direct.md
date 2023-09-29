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
{!> docs_src/nats/direct.py !}
```

### Consumer Announcement

To begin with, we have declared several consumers for two `subjects`: `test-subj-1` and `test-subj-2`:

```python linenums="7" hl_lines="1 5 9"
{!> docs_src/nats/direct.py [ln:7-17]!}
```

!!! note
    Note that all consumers are subscribed using the same `queue_group`. Within the same service, this does not make sense, since messages will come to these handlers in turn.
    Here, we emulate the work of several consumers and load balancing between them.

### Message Distribution

Now the distribution of messages between these consumers will look like this:

```python
{!> docs_src/nats/direct.py [ln:21]!}
```

The message `1` will be sent to `handler1` or `handler2` because they are listening to one `subject` within one `queue group`.

---

```python
{!> docs_src/nats/direct.py [ln:22]!}
```

Message `2` will be sent similarly to message `1`.

---

```python
{!> docs_src/nats/direct.py [ln:23]!}
```

The message `3` will be sent to `handler3` because it is the only one listening to `test-subj-2`.
