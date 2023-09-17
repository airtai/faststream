# Kafka routing

## Kafka Overview

### What is Kafka?

[Kafka](https://kafka.apache.org/){.external-link target="_blank"} is an open-source distributed streaming platform developed by the Apache Software Foundation. It is designed to handle high-throughput, fault-tolerant, real-time data streaming. Kafka is widely used for building real-time data pipelines and streaming applications.

### Key Kafka Concepts

#### 1. Publish-Subscribe Model

Kafka is built around the publish-subscribe messaging model. In this model, data is published to topics, and multiple consumers can subscribe to these topics to receive the data. This decouples the producers of data from the consumers, allowing for flexibility and scalability.

#### 2. Topics

A **topic** in Kafka is a logical channel or category to which messages are published by producers and from which messages are consumed by consumers. Topics are used to organize and categorize data streams. Each topic can have multiple **partitions**, which enable Kafka to distribute data and provide parallelism for both producers and consumers.

## Kafka Topics

### Understanding Kafka Topics

Topics are fundamental to Kafka and serve as the central point of data distribution. Here are some key points about topics:

- Topics allow you to logically group and categorize messages.
- Each message sent to Kafka is associated with a specific topic.
- Topics can have one or more partitions to enable parallel processing and scaling.
- Consumers subscribe to topics to receive messages.

### FastStream KafkaBroker

The FastStream KafkaBroker is a key component of the FastStream library that enables seamless integration with Apache Kafka. With the KafkaBroker, developers can easily connect to Kafka brokers, produce messages to Kafka topics, and consume messages from Kafka topics within their FastStream applications.

### Establishing a Connection

To connect to Kafka using the FastStream KafkaBroker module, follow these steps:

1. **Initialize the KafkaBroker instance:** Start by initializing a KafkaBroker instance with the necessary configuration, including Kafka broker address.

2. **Create your processing logic:** Write a function that will consume the incoming messages in the defined format and produce a response to the defined topic

3. **Decorate your processing function:** To connect your processing function to the desired Kafka topics you need to decorate it with `#!python @broker.subscriber` and `#!python @broker.publisher` decorators. Now after you start your application, your processing function will be called whenever a new message in the subscribed topic is available and produce the function return value to the topic defined in the publisher decorator.

Here's a simplified code example demonstrating how to establish a connection to Kafka using FastStream's KafkaBroker module:

```python linenums="1"
from faststream import FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

@broker.subscriber("in-topic")
@broker.publisher("out-topic")
async def handle_msg(user: str, user_id: int) -> str:
    return f"User: {user_id} - {user} registered"
```

This minimal example illustrates how FastStream simplifies the process of connecting to Kafka and performing basic message processing from the **in_topic** to the **out-topic**. Depending on your specific use case and requirements, you can further customize your Kafka integration with FastStream to build robust and efficient streaming applications.

For more advanced configuration options and detailed usage instructions, please refer to the FastStream Kafka documentation and the [offical Kafka documentation](https://kafka.apache.org/){.external-link target="_blank"}.
