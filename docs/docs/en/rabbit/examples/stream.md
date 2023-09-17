# RabbitMQ Streams

*RabbitMQ* has a [Streams](https://www.rabbitmq.com/streams.html){.exteranl-link target="_blank"} feature, which logic is closely related to *Kafka* topics.

The main difference from regular *RabbitMQ* queues is that the messages are not deleted after consuming.

And **FastStream** supports this feature as well!

```python linenums="1" hl_lines="4 10-12 17"
{!> docs_src/rabbit/subscription/stream.py !}
```
