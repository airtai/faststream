# Basic Subscriber

If you know nothing about **RabbitMQ** and how it works you still able to use **FastStream RabbitBroker**.

Just use `@broker.subscriber` method with a string as a routing key.

```python linenums="1"
{!> docs_src/rabbit/subscription/index.py !}
```

This way all **FastStream** brokers are working: you don't need to learn them deeper if you want to *just send a message*

## RabbitMQ details

If you are already known about **RabbitMQ** logic, you should know about the example above inner logic too.
In this case **FastStream** creates or validates **routing_key** name queue and bind it to the **RabbitMQ** default exchange.

If you want to specify *queue*-*exchange* pair with any arguments, **FastStream** provides you with we ability to make it too.
You can use special `RabbitQueue` and `RabbitExchange` objects to setup any RabbitMQ queues, exchanges and bindings properties.
The examples of various exchanges usage you can find in the following articles.
