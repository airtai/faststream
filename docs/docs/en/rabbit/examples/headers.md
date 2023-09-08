# Header Exchange

**Header** Exchange is the most complex and flexible way to route messages in *RabbitMQ*. This `exchange` type sends messages
to queues in according the matching of a queues binding arguments  with message headers.

At the same time, if the queue listens to several consumers, messages will also be distributed among them.

## Example

```python linenums="1"
{!> docs_src/rabbit/subscription/header.py !}
```

### Consumer Announcement

To begin with, we announced our **Fanout** exchange and several queues that will listen to it:

```python linenums="7" hl_lines="1 5 9 13"
{!> docs_src/rabbit/subscription/header.py [ln:7-20]!}
```

The `x-match` argument indicates whether the arguments should match the message headers in whole or in part.

Then we signed up several consumers using the advertised queues to the `exchange` we created

```python linenums="22" hl_lines="1 5 9 13"
{!> docs_src/rabbit/subscription/header.py [ln:22-36]!}
```

!!! note
    `handler1` and `handler2` are subscribed to the same `exchange` using the same queue:
    within a single service, this does not make a sense, since messages will come to these handlers in turn.
    Here we emulate the work of several consumers and load balancing between them.

### Message distribution

Now the distribution of messages between these consumers will look like this:

```python linenums="40"
{!> docs_src/rabbit/subscription/header.py [ln:40]!}
```

Message `1` will be sent to `handler1`, because it listens to a queue whose `key` header matches the `key` header of the message

---

```python linenums="41"
{!> docs_src/rabbit/subscription/header.py [ln:41]!}
```

Message `2` will be sent to `handler2` because it listens to `exchange` using the same queue, but `handler1` is busy

---

```python linenums="42"
{!> docs_src/rabbit/subscription/header.py [ln:42]!}
```

Message `3` will be sent to `handler1` again, because it is currently free

---

```python linenums="43"
{!> docs_src/rabbit/subscription/header.py [ln:43]!}
```

Message `4` will be sent to `handler3`, because it listens to a queue whose `key` header coincided with the `key` header of the message

---

```python linenums="44"
{!> docs_src/rabbit/subscription/header.py [ln:44]!}
```

Message `5` will be sent to `handler3`, because it listens to a queue whose header `key2` coincided with the header `key2` of the message

---

```python linenums="45"
{!> docs_src/rabbit/subscription/header.py [ln:45-46]!}
```

Message `6` will be sent to `handler3` and `handler4`, because the message headers completely match the queue keys

---

!!! note
    When sending messages to **Header** exchange, it makes no sense to specify the arguments `queue` or `routing_key`, because they will be ignored

!!! warning
    For incredibly complex routes, you can use the option to bind an `exchange` to another `exchange`. In this case, all the same rules apply as for queues subscribed to `exchange`. The only difference is that the signed `exchange` can further distribute messages according to its own rules.

    So, for example, you can combine Topic and Header exchange types.
