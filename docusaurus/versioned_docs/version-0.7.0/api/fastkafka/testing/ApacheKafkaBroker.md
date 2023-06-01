## `fastkafka.testing.ApacheKafkaBroker` {#fastkafka.testing.ApacheKafkaBroker}


ApacheKafkaBroker class, used for running unique kafka brokers in tests to prevent topic clashing.

### `__init__` {#init}

`def __init__(self, topics: Iterable[str] = [], retries: int = 3, apply_nest_asyncio: bool = False, zookeeper_port: int = 2181, listener_port: int = 9092) -> None`

Initialises the ApacheKafkaBroker object

**Parameters**:
- `data_dir`: Path to the directory where the zookeepeer instance will save data
- `zookeeper_port`: Port for clients (Kafka brokes) to connect
- `listener_port`: Port on which the clients (producers and consumers) can connect

### `get_service_config_string` {#get_service_config_string}

`def get_service_config_string(self: fastkafka.testing.ApacheKafkaBroker, service: str, data_dir: pathlib.Path) -> str`

Gets the configuration string for a service.

**Parameters**:
- `service`: Name of the service ("kafka" or "zookeeper").
- `data_dir`: Path to the directory where the service will save data.

**Returns**:
- The service configuration string.

### `start` {#start}

`def start(self: fastkafka.testing.ApacheKafkaBroker) -> str`

Starts a local Kafka broker and ZooKeeper instance synchronously.

**Returns**:
- The Kafka broker bootstrap server address in string format: host:port.

### `stop` {#stop}

`def stop(self: fastkafka.testing.ApacheKafkaBroker) -> None`

Stops a local kafka broker and zookeeper instance synchronously

**Returns**:
- None

