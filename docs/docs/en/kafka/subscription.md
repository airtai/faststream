# Basic Subscriber

To start consuming from a Kafka topic just decorate your consuming function with a `@broker.subscriber(...)` decorator passing a string as a topic key.

In the folowing example we will create a simple FastStream app that will consume `HelloWorld` messages from a **hello_world** topic.

The full app code looks like this:

```python
    {!> docs_src/kafka/consumes_basics/app.py!}
```
