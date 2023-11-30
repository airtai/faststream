# Redis List Publishing with FastStream

Utilizing the **FastStream** library, you can effectively publish data to Redis lists, which act as queues in Redis-based messaging systems.

## Understanding Redis List Publishing

Just like with Redis streams, messages can be published to Redis lists. FastStream utilizes the `@broker.publisher` decorator, along with a list's name, to push messages onto the list.

1. Instantiate your RedisBroker

    ```python linenums="1"
    {!> docs_src/redis/list_pub/app.py [ln:13] !}
    ```

1. Create your FastStream application with the instantiated RedisBroker

    ```python linenums="1"
    {!> docs_src/redis/list_pub/app.py [ln:14] !}
    ```

1. Define a Pydantic model for your data

    ```python linenums="1"
    {!> docs_src/redis/list_pub/app.py [ln:7-10] !}
    ```

1. Implement a data processing function for publishing to Redis lists

    Use the `@broker.publisher(list="...")` decorator alongside the `@broker.subscriber(list="...")` decorator to create a function that processes incoming messages and pushes the results to an output list in Redis.

    ```python linenums="1"
    {!> docs_src/redis/list_pub/app.py [ln:17-20] !}
    ```

In this pattern, the function stands as a subscriber to the "input-list" and publishes the processed data as a new message to the "output-list." By using decorators, you establish a pipeline that reads messages from one Redis list, applies some logic, and then pushes outputs to another list.

## Full Example of Redis List Publishing

Here's an example that demonstrates Redis list publishing in action using decorators with FastStream:

```python linenums="1"
{!> docs_src/redis/list_pub/app.py !}
```

The provided example illustrates the ease of setting up publishing mechanisms to interact with Redis lists. In this environment, messages are dequeued from the input list, processed, and enqueued onto the output list seamlessly, empowering developers to leverage Redis lists as messaging queues.

By following these simple steps, you can perform list-based publish/subscribe operations in a Redis environment using the FastStream library, capitalizing on Redis' fast, in-memory data structure store capabilities.
