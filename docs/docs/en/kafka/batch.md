# Batch publishing

If you want to send your data in batches `broker.publisher` makes that possible for you. By returning a tuple of messages you want to send in a batch the publisher will collect the messages and send them in a batch to a Kafka broker.

This guide will demonstrate how to use this feature.

## Return a batch from the publishing function

To define a batch that you want to produce to Kafka topic, you need to set the `batch` parameter of the publisher to `True` and return a tuple of messages that you want to send in a batch.

``` python hl_lines="1 7-10"
{!> docs_src/kafka/basic/basic.py[ln:1-10]!}

# Code below omitted 👇
```

<details>
<summary>👀 Full file preview</summary>

``` python
{!> docs_src/kafka/basic/basic.py!}
```

</details>
