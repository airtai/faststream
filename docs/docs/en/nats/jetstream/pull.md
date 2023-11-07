# Pull Subscriber

## Overview

**NATS JetStream** supports two various way to consume messages: **Push** and [**Pull**](https://docs.nats.io/using-nats/developer/develop_jetstream/consumers#push-and-pull-consumers){.external-link targer="_blank} consumers.

**Push** consumer is using by default to consume messages with the **FastStream**. It means, that **NATS** server delivers messages to your consumer as far as possible by itself. But also it means, that **NATS** should control all current consumer connections and increase server load.

Thus, **Pull** consumer is a recommended by *NATS TEAM* way to consume JetStream messages. Using it, you just asking **NATS** for a new messages with a some interval. It sounds a little bit worse than the automatic message delivery, but it provides you with a several advantages:

* consumer scaling without *queue group*
* handle messages in batches
* reduce **NATS** server load

So, if you want to consume a huge messages flow without strict time limitations, **Pull** consumer is the right choice for you.

## FastStream details

**Pull** consumer is just a regular *Stream* consumer, but with the `pull_sub` argument, controls consuming messages batch size and block interval.

```python linenums="1" hl_lines="10-11"
{!> docs_src/nats/js/pull_sub.py !}
```

Batch size doesn't mean that your `msg` argument is a list of messages, but it means, that you consume up to `10` messages for one request to **NATS** and call your handler per each message in an `asyncio.gather` pool.

So, your subject will be processed much faster, without blocking per message processing. But, if your subject has less than `10` messages, your reguest to **NATS** will be blocked for `timeout` (5 seconds by default) trying to collect required messages amount. So, you should choise `batch_size` and `timeout` accurately to optimize your consumer efficiency.
