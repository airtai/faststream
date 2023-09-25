# RPC over RMQ

## Blocking Request

**FastStream** provides you with the ability to send a blocking RPC request over *RabbitMQ* in a very simple way.

It uses the [**Direct Reply-To**](https://www.rabbitmq.com/direct-reply-to.html){.external-link target="_blank"} *RabbitMQ* feature, so you don't need to create any queues to consume a response.

Just send a message like a regular one and get a response synchronously.

It is very close to common **requests** syntax:

``` python hl_lines="1 4"
msg = await broker.publish(
    "Hi!",
    queue="test",
    rpc=True,
)
```

Also, you have two extra options to control this behavior:

* `#!python rpc_timeout: Optional[float] = 30.0` - controls how long you are waiting for a response
* `#!python raise_timeout: bool = False` - by default, a timeout request returns `None`, but if you need to raise a TimeoutException directly, you can specify this option

## Reply-To

Also, if you want to create a permanent request-reply data flow, probably, you should create a permanent queue to consume responses.

So, if you have such one, you can specify it with the `reply_to` argument. This way, **FastStream** will send a response to this queue automatically.

``` python hl_lines="1 8"
@broker.subscriber("response-queue")
async def consume_responses(msg):
    ...

msg = await broker.publish(
    "Hi!",
    queue="test",
    reply_to="response-queue",
)
```
