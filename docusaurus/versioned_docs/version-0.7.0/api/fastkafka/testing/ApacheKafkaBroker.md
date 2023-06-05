## `fastkafka.testing.ApacheKafkaBroker` {#fastkafka.testing.ApacheKafkaBroker}


ApacheKafkaBroker class, used for running unique kafka brokers in tests to prevent topic clashing.

### `__init__` {#init}

```py
__init__(
    self,
    topics=[],
    retries=3,
    apply_nest_asyncio=False,
    zookeeper_port=2181,
    listener_port=9092,
)
```

Initialises the ApacheKafkaBroker object

**Parameters**:
- `data_dir`: Path to the directory where the zookeepeer instance will save data
- `zookeeper_port`: Port for clients (Kafka brokes) to connect
- `listener_port`: Port on which the clients (producers and consumers) can connect

### `get_service_config_string` {#get_service_config_string}

```py
get_service_config_string(self, service, data_dir)
```

Gets the configuration string for a service.

**Parameters**:
- `service`: Name of the service ("kafka" or "zookeeper").
- `data_dir`: Path to the directory where the service will save data.

**Returns**:
- The service configuration string.

### `start` {#start}

```py
start(self)
```

Starts a local Kafka broker and ZooKeeper instance synchronously.

**Returns**:
- The Kafka broker bootstrap server address in string format: host:port.

### `stop` {#stop}

```py
stop(self)
```

Stops a local kafka broker and zookeeper instance synchronously

**Returns**:
- None

