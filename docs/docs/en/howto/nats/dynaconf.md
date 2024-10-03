---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# DyncConf with Nats

As Nats have key-value storage, you can use it as a configuration storage. Here is an example of how you can use it with **FastStream**.

## Subscribing to Key-Value Changes

For subscribing to key-value changes, you can use the `KvWatch` class, to subject we must pass key is key in storage.

When we receive a message, we can update the global context with the new value.

```python linenums="1" hl_lines="7-9"
from faststream import FastStream
from faststream.nats import NatsBroker, KvWatch

broker = NatsBroker()
app = FastStream(broker)

@broker.subscriber("create_sell", kv_watch=KvWatch("order_service"))
async def watch_kv_order_service(new_value: str):
    app.context.set_global("create_sell", bool(int(new_value)))
```

## Checking the parameter in the subscriber

We can use `faststream.Context` to get parameter from global context.

```python linenums="1" hl_lines="8-10"
from faststream import FastStream, Context
from faststream.nats import NatsBroker, NatsMessage

broker = NatsBroker()
app = FastStream(broker)

@broker.subscriber("order_service.order.filled.buy")
async def handle_filled_buy(message: NatsMessage, create_sell: bool = Context("create_sell")):
    if create_sell:
        await broker.publish(b"", "order_service.order.create.sell")
```

!!! note
    KeyValue watcher will receive latest value on startup

??? example "Full Class Example"
    ```python linenums="1"
    from uuid import uuid4

    from faststream import FastStream, Context
    from faststream.nats import NatsMessage, NatsBroker, KvWatch
    
    broker = NatsBroker()
    app = FastStream(broker)
    
    
    @broker.subscriber("create_sell", kv_watch=KvWatch("order_service"))
    async def watch_kv_order_service(new_value: str):
        app.context.set_global("create_sell", bool(int(new_value)))
    
    
    @broker.subscriber("order_service.order.filled.buy")
    async def handle_filled_buy(message: NatsMessage, create_sell: bool = Context("create_sell")):
        print(message)
        if create_sell:
            await broker.publish(b"", "order_service.order.create.sell")
    
    
    @broker.subscriber("order_service.order.create.sell")
    async def handle_create_sell(message: NatsMessage): ...
    
    
    @app.on_startup
    async def on_startup():
        await broker.connect()
    
        order_service_kv = await broker.key_value("order_service")
        await order_service_kv.put("create_sell", b"1")
    
        app.context.set_global("create_sell", bool(int((await order_service_kv.get("create_sell")).value)))
    
    
    @app.after_startup
    async def after_startup():
        await broker.publish({"order_id": str(uuid4())}, "order_service.order.filled.buy")
    ```
