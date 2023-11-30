# Redis Broker

## Redis Overview

### What is Redis?

[Redis](https://redis.io/){.external-link target="_blank"} is an open-source, in-memory data structure store, used as a database, cache, and message broker. It supports various data structures such as strings, hashes, lists, sets, sorted sets, bitmaps, hyperloglogs, and geospatial indexes with radius queries. Redis has built-in replication, Lua scripting, LRU eviction, transactions, and different levels of on-disk persistence, and provides high availability via Redis Sentinel and automatic partitioning with Redis Cluster.

### Key Redis Concepts

#### 1. Data Structures

Redis is not just a key-value store; it is a data structures server, supporting different kinds of values. This makes Redis flexible and suitable for a wide range of problems.

#### 2. Pub/Sub

Redis Pub/Sub implements the Publish/Subscribe messaging paradigm where senders (publishers) are not programmed to send their messages to specific receivers (subscribers). Instead, published messages are characterized into channels, without knowledge of what (if any) subscribers there may be.

## Redis in FastStream

### FastStream RedisBroker

The FastStream RedisBroker is a key component of the FastStream framework that enables seamless integration with Redis. With the RedisBroker, developers can easily connect to Redis instances, publish messages to Redis channels, and subscribe to Redis channels within their FastStream applications.

### Establishing a Connection

To connect to Redis using the FastStream RedisBroker module, follow these steps:

1. **Initialize the RedisBroker instance:** Start by initializing a RedisBroker instance with the necessary configuration, including Redis server address and port.

2. **Create your processing logic:** Write a function that will consume the incoming messages from the subscribed channel and optionally publish a response to another channel.

3. **Decorate your processing function:** To connect your processing function to the desired Redis channels, you need to decorate it with `#!python @broker.subscriber` and `#!python @broker.publisher` decorators. Now, after you start your application, your processing function will be called whenever a new message in the subscribed channel is available and produce the function return value to the channel defined in the publisher decorator.

Here's a simplified code example demonstrating how to establish a connection to Redis using FastStream's RedisBroker module:

```python linenums="1"
{!> docs_src/index/redis/basic.py!}
```

This minimal example illustrates how FastStream simplifies the process of connecting to Redis and performing basic message processing from the **in-channel** to the **out-channel**. Depending on your specific use case and requirements, you can further customize your Redis integration with FastStream to build efficient and responsive applications.

For more advanced configuration options and detailed usage instructions, please refer to the FastStream Redis documentation and the [official Redis documentation](https://redis.io/documentation){.external-link target="_blank"}.
