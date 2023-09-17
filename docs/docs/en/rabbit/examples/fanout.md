# Fanout Exchange

**Fanout** Exchange is an even simpler, but slightly less popular way of routing in *RabbitMQ*. This type of `exchange` sends messages to all queues subscribed to it, ignoring any arguments of the message.

At the same time, if the queue listens to several consumers, messages will also be distributed among them.

## Example

```python linenums="1"
{!> docs_src/rabbit/subscription/fanout.py !}
```

### Consumer Announcement

To begin with, we announced our **Fanout** exchange and several queues that will listen to it:

```python linenums="7" hl_lines="1"
{!> docs_src/rabbit/subscription/fanout.py [ln:7-10]!}
```

Then we signed up several consumers using the advertised queues to the `exchange` we created

```python linenums="13" hl_lines="1 6 11"
{!> docs_src/rabbit/subscription/fanout.py [ln:13-25]!}
```

!!! note
    `handler1` and `handler2` are subscribed to the same `exchange` using the same queue:
    within a single service, this does not make a sense, since messages will come to these handlers in turn.
    Here we emulate the work of several consumers and load balancing between them.

### Message distribution

Now the distribution of messages between these consumers will look like this:

```python linenums="30"
{!> docs_src/rabbit/subscription/fanout.py [ln:30]!}
```

Message `1` will be sent to `handler1` and `handler3`, because they listen to `exchange` using different queues

---

```python linenums="31"
{!> docs_src/rabbit/subscription/fanout.py [ln:31]!}
```

Message `2` will be sent to `handler2` and `handler3`, because `handler2` listens to `exchange` using the same queue as `handler1`

---

```python linenums="32"
{!> docs_src/rabbit/subscription/fanout.py [ln:32]!}
```

Message `3` will be sent to `handler1` and `handler3`

---

```python linenums="33"
{!> docs_src/rabbit/subscription/fanout.py [ln:33]!}
```

Message `4` will be sent to `handler3` and `handler3`

---

!!! note
    When sending messages to **Fanout** exchange, it makes no sense to specify the arguments `queue` or `routing_key`, because they will be ignored
