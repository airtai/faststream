## `fastkafka.testing.LocalRedpandaBroker` {#fastkafka.testing.LocalRedpandaBroker}


LocalRedpandaBroker class, used for running unique redpanda brokers in tests to prevent topic clashing.

### `__init__` {#init}

```py
__init__(
    self,
    topics=[],
    retries=3,
    apply_nest_asyncio=False,
    listener_port=9092,
    tag="v23.1.2",
    seastar_core=1,
    memory="1G",
    mode="dev-container",
    default_log_level="debug",
    kwargs,
)
```

Initialises the LocalRedpandaBroker object

**Parameters**:
- `listener_port`: Port on which the clients (producers and consumers) can connect
- `tag`: Tag of Redpanda image to use to start container
- `seastar_core`: Core(s) to use byt Seastar (the framework Redpanda uses under the hood)
- `memory`: The amount of memory to make available to Redpanda
- `mode`: Mode to use to load configuration properties in container
- `default_log_level`: Log levels to use for Redpanda

### `get_service_config_string` {#get_service_config_string}

```py
get_service_config_string(self, service, data_dir)
```

Generates a configuration for a service

**Parameters**:
- `data_dir`: Path to the directory where the zookeepeer instance will save data
- `service`: "redpanda", defines which service to get config string for

### `start` {#start}

```py
start(self)
```

Starts a local redpanda broker instance synchronously

**Returns**:
- Redpanda broker bootstrap server address in string format: add:port

### `stop` {#stop}

```py
stop(self)
```

Stops a local redpanda broker instance synchronously

**Returns**:
- None

