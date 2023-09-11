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
{!> docs_src/rabbit/subscription/direct.py !}
```

### Consumer Announcement

To begin with, we announced our **Direct** exchange and several queues that will listen to it:

```python linenums="7"
{!> docs_src/rabbit/subscription/direct.py [ln:7-10]!}
```

Then we signed up several consumers using the advertised queues to the `exchange` we created

```python linenums="12" hl_lines="1 5 9"
{!> docs_src/rabbit/subscription/direct.py [ln:12-22]!}
```

!!! note
    `handler1` and `handler2` are subscribed to the same `exchange` using the same queue:
    within a single service, this does not make a sense, since messages will come to these handlers in turn.
    Here we emulate the work of several consumers and load balancing between them.

### Message distribution

Now the distribution of messages between these consumers will look like this:

```python linenums="26"
{!> docs_src/rabbit/subscription/direct.py [ln:26]!}
```

Message `1` will be sent to `handler1` because it listens to `exchange` using a queue with the routing key `test-q-1`

---

```python linenums="27"
{!> docs_src/rabbit/subscription/direct.py [ln:27]!}
```

Message `2` will be sent to `handler2` because it listens to `exchange` using the same queue, but `handler1` is busy

---

```python linenums="28"
{!> docs_src/rabbit/subscription/direct.py [ln:28]!}
```

Message `3` will be sent to `handler1` again, because it is currently free

---

```python linenums="29"
{!> docs_src/rabbit/subscription/direct.py [ln:29]!}
```

Message `4` will be sent to `handler3`, because it is the only one listening to `exchange` using a queue with the routing key `test-q-2`
