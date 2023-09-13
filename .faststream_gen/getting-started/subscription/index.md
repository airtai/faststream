# Subscription Basics

Topic/queue/subject/etc agnostic. The same syntax in a basic cases for all brokers:

=== "Kafka"
    Hi

=== "RabbitMQ"
    Hi

Consumes a message body in the arguments, serialize it based on type annotations by the Pydantic.
Allows to get access to the raw message and specific fields via the [Context](../context/existed.md){.internal-link} if it is required.

Disable pydantic validation by `apply_types=False` (disables Context and Depends too)

## Multiple Subscriptions

```python
@broker.subscriber("first_sub")
@broker.subscriber("second_sub")
async def handler(msg):
    ...
```
