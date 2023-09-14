# Application and Access Logging

**FastStream** uses 2 previously configured loggers:

* `faststream` - using by `FastStream` app
* `faststream.access` - using by broker

## Logging requests

To log requests, it is strongly recommended to use the `access_logger` of your broker, since it is available from the [Context](../getting-started/context/existed.md){.internal-link} of your application.

```python
from faststream import Logger
from faststream.rabbit import RabbitBroker

broker = RabbitBroker()

@broker.subscriber("test")
async def func(logger: Logger):
    logger.info("message received")
```

This approach has several advantages:

* the logger already contains the request context: message ID, broker-based params
* by replacing the `logger` at broker initializing, you will automatically replace all loggers inside your functions

## Logging levels

If you use the **FastStream CLI**, you can change the current logging level of the entire application directly from the command line.

The `--log-level` flag sets the current logging level for both a broker and a `FastStream` app. This way you can configure the levels of not only default loggers, but also your own, if you use them inside **FastStream**

```console
faststream run serve:app --log-level debug
```

If you want to completely disable the default logging of `Propan`, you can set `logger=None`

```python
from faststream import FastStream
from faststream.rabbit import RabbitBroker

broker = RabbitBroker(logger=None) # disables broker logs
app = FastStream(broker, logger=None) # disables application logs
```

!!! warning
    Be careful: the `logger` that you get from the context will also have the value `None' if you turn off the broker logging

If you don't want to lose access to the `logger' inside your context, but want to get rid of the default logs **FastStream**, you can lower the level of logs that the broker publishes itself.

```python
import logging
from faststream.rabbit import RabbitBroker

# sets the broker logs to the DEBUG level
broker = RabbitBroker(log_level=logging.DEBUG)
```

## Formatting logs

If you are not satisfied with the current format of your application logs, you can change it directly in your broker's constructor

```python
from faststream.rabbit import RabbitBroker
broker = RabbitBroker(log_fmt="%(asctime)s %(levelname)s - %(message)s")
```

## Using your own loggers

Since **FastStream** works with the standard `logging.Logger` object, you can initiate an application and a broker
using your own logger

```python
import logging
from faststream import FastStream
from faststream.rabbit import RabbitBroker

logger = logging.getLogger("my_logger")

broker = RabbitBroker(logger=logger)
app = FastStream(broker, logger=logger)
```

Doing so, you will lose information about the context of the current request. However, you can get it directly from the context anywhere in your code:

```python
from faststream import context
log_context: dict[str, str] = context.get_local("log_context")
```

## Logger access

If you want to override default loggers behavior, you can access them directly via `logging`:

```python
import logging
logger = logging.getLogger("faststream")
access_logger = logging.getLogger("faststream.access")
```

Or by importing them from **FastStream**

```python
from faststream.log import access_logger, logger
```
