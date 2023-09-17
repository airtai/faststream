# Batch Subscriber

If you want to consume data in batches `#!python @broker.subscriber(...)` decorator makes that possible for you. By typing a consumed msg object as a list of messages and setting the `batch` parameter to `True` the subscriber will call your consuming function with a batch of messages consumed from a single partition. Let’s demonstrate that now.

## Subscriber function with batching

To consume messages in batches, you need to wrap you message type into a list and and set the `batch` parameter to `True`, the `#!python @broker.subscriber(...)` decorator will take care of the rest for you. Your subscribed function will be called with batches grouped by partition now.

Here is an example of consuming in batches from **test_batch** topic:

```python linenums="1"
@broker.subscriber("test_batch", batch=True)
async def handle_batch(msg: List[HelloWorld], logger: Logger):
    logger.info(msg)
```
