---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# RPC over NATS

Because **NATS** has zero cost for creating new subjects, we can easily set up a new subject consumer just for the one response message. This way, your request message will be published to one topic, and the response message will be consumed from another one (temporary subject), which allows you to use regular **FastStream RPC** syntax in the **NATS** case too.

!!! tip
    **FastStream RPC** over **NATS** works in both the *NATS-Core* and *NATS-JS* cases as well, but in the *NATS-JS* case, you have to specify the expected `stream` as a publish argument.

## Blocking Request

**FastStream** provides you with the ability to send a blocking RPC request over *NATS* in a very simple way.

Just send a message like a regular one and get a response synchronously.

It is very close to the common **requests** syntax:

```python hl_lines="3"
from faststream.nats import NatsMessage

msg: NatsMessage = await broker.request(
    "Hi!",
    subject="test",
)
```

## Reply-To

Also, if you want to create a permanent request-reply data flow, probably, you should create a permanent subject to consume responses.

So, if you have such one, you can specify it with the `reply_to` argument. This way, **FastStream** will send a response to this subject automatically.

```python hl_lines="1 8"
@broker.subscriber("response-subject")
async def consume_responses(msg):
    ...

await broker.publish(
    "Hi!",
    subject="test",
    reply_to="response-subject",
)
```
