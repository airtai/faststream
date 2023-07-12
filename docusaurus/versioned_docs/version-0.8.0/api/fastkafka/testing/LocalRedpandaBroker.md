## fastkafka.testing.LocalRedpandaBroker {#fastkafka.testing.LocalRedpandaBroker}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/local_redpanda_broker.py#L84-L200" class="link-to-source" target="_blank">View source</a>


LocalRedpandaBroker class, used for running unique redpanda brokers in tests to prevent topic clashing.

### __init__ {#fastkafka._testing.local_redpanda_broker.LocalRedpandaBroker.init}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/local_redpanda_broker.py#L88-L120" class="link-to-source" target="_blank">View source</a>

```py
__init__(
    self,
    topics=[],
    retries=3,
    apply_nest_asyncio=False,
    listener_port=9092,
    tag='v23.1.2',
    seastar_core=1,
    memory='1G',
    mode='dev-container',
    default_log_level='debug',
    kwargs,
)
```

Initialises the LocalRedpandaBroker object

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `topics` | `Iterable[str]` | List of topics to create after sucessfull redpanda broker startup | `[]` |
| `retries` | `int` | Number of retries to create redpanda service | `3` |
| `apply_nest_asyncio` | `bool` | set to True if running in notebook | `False` |
| `listener_port` | `int` | Port on which the clients (producers and consumers) can connect | `9092` |
| `tag` | `str` | Tag of Redpanda image to use to start container | `'v23.1.2'` |
| `seastar_core` | `int` | Core(s) to use byt Seastar (the framework Redpanda uses under the hood) | `1` |
| `memory` | `str` | The amount of memory to make available to Redpanda | `'1G'` |
| `mode` | `str` | Mode to use to load configuration properties in container | `'dev-container'` |
| `default_log_level` | `str` | Log levels to use for Redpanda | `'debug'` |

### get_service_config_string {#fastkafka._testing.local_redpanda_broker.LocalRedpandaBroker.get_service_config_string}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/local_redpanda_broker.py#L168-L174" class="link-to-source" target="_blank">View source</a>

```py
get_service_config_string(
    self, service, data_dir
)
```

Generates a configuration for a service

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `data_dir` | `Path` | Path to the directory where the zookeepeer instance will save data | *required* |
| `service` | `str` | "redpanda", defines which service to get config string for | *required* |

### is_started {#fastkafka._testing.local_redpanda_broker.LocalRedpandaBroker.is_started}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/local_redpanda_broker.py#L123-L133" class="link-to-source" target="_blank">View source</a>

```py
@property
is_started(
    self
)
```

Property indicating whether the LocalRedpandaBroker object is started.

The is_started property indicates if the LocalRedpandaBroker object is currently
in a started state. This implies that Redpanda docker container has sucesfully
started and is ready for handling events.

**Returns**:

|  Type | Description |
|---|---|
| `bool` | True if the object is started, False otherwise. |

### start {#fastkafka._testing.local_redpanda_broker.LocalRedpandaBroker.start}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/local_redpanda_broker.py#L333-L372" class="link-to-source" target="_blank">View source</a>

```py
start(
    self
)
```

Starts a local redpanda broker instance synchronously

**Returns**:

|  Type | Description |
|---|---|
| `str` | Redpanda broker bootstrap server address in string format: add:port |

### stop {#fastkafka._testing.local_redpanda_broker.LocalRedpandaBroker.stop}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/local_redpanda_broker.py#L376-L388" class="link-to-source" target="_blank">View source</a>

```py
stop(
    self
)
```

Stops a local redpanda broker instance synchronously

