---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# RabbitMQ Queue/Exchange Declaration

**FastStream** *subscribers* declares and validates all using *RabbitMQ* exchanges and queues (*publishers* declares exchanges only), but sometimes you need to declare them manually.

**RabbitBroker** provides a way to achieve this easily.

```python linenums="1" hl_lines="15-20 22-27"
{! docs_src/rabbit/declare.py !}
```

These methods require just one argument (`RabbitQueue`/`RabbitExchange`) containing information about your *RabbitMQ* required objects. They declare/validate *RabbitMQ* objects and return low-level **aio-pika** robust objects to interact with.

!!! tip
    Also, these methods are idempotent, so you can call them with the same arguments multiple times, but the objects will be created once; next time the method will return an already stored object. This way you can get access to any queue/exchange created automatically.


# RabbitMQ Queue/Exchange Binding Declaration

It is also possible to declare a binding between a queue and an exchange. Same as with previous methods, it keeps indepodent. If not previously declared, they will automatically be declared as in the following example:

```python linenums="1" hl_lines="15-20 22-27"
{! docs_src/rabbit/bind.py !}
```