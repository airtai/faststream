# RPC over RMQ

## Blocking request

**FastStream** provides you with the ability to send low-cost blocking RPC request over *RabbitMQ* in a very simple way.

It uses the [**Direct Reply-To**](https://www.rabbitmq.com/direct-reply-to.html){.external-link target="_blank"} *RabbitMQ* feature, so you need no to create any queues to consume a response.

Just send a message like a regular one and get a response synchronously.

It is a very close to common **requests** syntax, so you shouldn't have any problems with it

``` python hl_lines="1 4"
msg = await broker.publish(
    "Hi!",
    queue="test",
    rpc=True,
)
```

Also, you have a two extra options to control this behavior:

* `#!python rpc_timeout: Optional[float] = 30.0` - controls how long you are waiting for response
* `#!python raise_timeout: bool = False` - by default timeout request returns `None`, but if you need to raise TimeoutException directly, you can specify this option

## Reply-To

Also, if you want to create permanent request-reply data flow, probably, you should create a permanent queue to consume responses.

So, if you have a such one, you can specify it with `reply_to` argument. This way **FastStream** will send a response in this queue automatically.


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
