# Basic Subscriber

If you know nothing about **RabbitMQ** and how it works you still able to use **FastStream RabbitBroker**.

Just use `#!python @broker.subscriber(...)` method with a string as a routing key.

```python linenums="1"
{!> docs_src/rabbit/subscription/index.py !}
```

This way all **FastStream** brokers are working: you don't need to learn them deeper if you want to *just send a message*

## RabbitMQ details

If you are already familiar with the **RabbitMQ** logic, you should also understand the inner logic explained above. In this case, **FastStream** creates or validates a queue with the specified **routing_key** name and binds it to the **RabbitMQ** default exchange.

If you want to specify a *queue*-*exchange* pair with additional arguments, **FastStream** provides you with the ability to do so. You can use the special `RabbitQueue` and `RabbitExchange` objects to configure RabbitMQ queues, exchanges, and binding properties. Examples of various exchange usages can be found in the following articles.
