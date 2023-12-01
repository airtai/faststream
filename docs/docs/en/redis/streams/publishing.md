# Redis Stream Publishing with FastStream

## Publishing Data to Redis Stream

To publish messages to a Redis Stream, you implement a function that processes the incoming data and applies the `@broker.publisher` decorator along with the Redis stream name to it. The function will then publish its return value to the specified stream.

1. Create your RedisBroker instance

    ```python linenums="1"
    {!> docs_src/redis/stream/pub.py [ln:13] !}
    ```

1. Initiate your FastStream application with the RedisBroker

    ```python linenums="1"
    {!> docs_src/redis/stream/pub.py [ln:14] !}
    ```

1. Define your data model

    ```python linenums="1"
    {!> docs_src/redis/stream/pub.py [ln:7-10] !}
    ```

1. Set up the function for data processing and publishing

    Using the `@broker.publisher()` decorator in conjunction with the `@broker.subscriber()` decorator allows seamless message processing and republishing to a different stream.

    ```python linenums="1"
    {!> docs_src/redis/stream/pub.py [ln:17-20] !}
    ```

    By decorating a function with `@broker.publisher`, we tell FastStream to publish the function's returned data to the designated output stream. The defined function also serves as a subscriber to the `input-stream`, thereby setting up a straightforward data pipeline within Redis streams.

Here's the complete example that showcases the use of decorators for both subscribing and publishing to Redis streams:

```python linenums="1"
{!> docs_src/redis/stream/pub.py !}
```
