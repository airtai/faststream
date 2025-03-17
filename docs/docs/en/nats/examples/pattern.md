---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Pattern

[**Pattern**](https://docs.nats.io/nats-concepts/subjects#wildcards){.external-link target="_blank"} Subject is a powerful *NATS* routing engine. This type of `subject` routes messages to consumers based on the *pattern* specified when they connect to the `subject` and a message key.

## Scaling

If one `subject` is being listened to by several consumers with the same `queue group`, the message will go to a random consumer each time.

Thus, *NATS* can independently balance the load on queue consumers. You can increase the processing speed of the message flow from the queue by simply launching additional instances of the consumer service. You don't need to make changes to the current infrastructure configuration: *NATS* will take care of how to distribute messages between your services.

!!! tip
    By default, all subscribers are consuming messages from subject in blocking mode. You can't process multiple messages from the same subject in the same time. So, you have some kind of block per subject.

    But, all `NatsBroker` subscribers has `max_workers` argument allows you to consume messages in a per-subscriber pool. So, if you have subscriber like `#!python @broker.subscriber(..., max_workers=10)`, it means that you can process up to **10** by it in the same time.


## Example

```python linenums="1"
{! docs_src/nats/pattern.py [ln:1-12.42,13-] !}
```

### Consumer Announcement

To begin with, we have announced several consumers for two `subjects`: `#!python "*.info"` and `#!python "*.error"`:

```python linenums="7" hl_lines="1 5 9"
{! docs_src/nats/pattern.py [ln:7-12.42,13-17] !}
```

At the same time, in the `subject` of our consumers, we specify the *pattern* that will be processed by these consumers.

!!! note
    Note that all consumers are subscribed using the same `queue_group`. Within the same service, this does not make sense, since messages will come to these handlers in turn.
    Here, we emulate the work of several consumers and load balancing between them.

### Message Distribution

Now the distribution of messages between these consumers will look like this:

```python
{! docs_src/nats/pattern.py [ln:21.5] !}
```

The message `1` will be sent to `handler1` or `handler2` because they listen to the same `subject` template within the same `queue group`.

---

```python
{! docs_src/nats/pattern.py [ln:22.5] !}
```

Message `2` will be sent similarly to message `1`.

---

```python
{! docs_src/nats/pattern.py [ln:23.5] !}
```

The message `3` will be sent to `handler3` because it is the only one listening to the pattern `#!python "*.error"`.
