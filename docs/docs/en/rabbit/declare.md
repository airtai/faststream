# RabbitMQ Queue/Exchange Declaration

**FastStream** declares and validates all exchanges and queues using *publishers* and *subscribers* *RabbitMQ* objects, but sometimes you need to declare them manually.

**RabbitBroker** provides a way to achieve this easily.

``` python linenums="1" hl_lines="15-20 22-27"
{!> docs_src/rabbit/declare.py !}
```

These methods require just one argument (`RabbitQueue`/`RabbitExchange`) containing information about your *RabbitMQ* required objects. They declare/validate *RabbitMQ* objects and return low-level **aio-pika** robust objects to interact with.

!!! tip
    Also, these methods are idempotent, so you can call them with the same arguments multiple times, but the objects will be created once; next time the method will return an already stored object. This way you can get access to any queue/exchange created automatically.
