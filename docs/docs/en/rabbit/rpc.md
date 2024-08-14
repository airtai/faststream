---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# RPC over RMQ

## Blocking Request

**FastStream** provides you with the ability to send a blocking RPC request over *RabbitMQ* in a very simple way.

It uses the [**Direct Reply-To**](https://www.rabbitmq.com/direct-reply-to.html){.external-link target="_blank"} *RabbitMQ* feature, so you don't need to create any queues to consume a response.

Just send a message like a regular one and get a response synchronously.

It is very close to common **requests** syntax:

```python hl_lines="3"
from faststream.rabbit import RabbitMessage

msg: RabbitMessage = await broker.request(
    "Hi!",
    queue="test",
)
```

## Reply-To

Also, if you want to create a permanent request-reply data flow, probably, you should create a permanent queue to consume responses.

So, if you have such one, you can specify it with the `reply_to` argument. This way, **FastStream** will send a response to this queue automatically.

```python hl_lines="1 8"
@broker.subscriber("response-queue")
async def consume_responses(msg):
    ...

msg = await broker.publish(
    "Hi!",
    queue="test",
    reply_to="response-queue",
)
```
