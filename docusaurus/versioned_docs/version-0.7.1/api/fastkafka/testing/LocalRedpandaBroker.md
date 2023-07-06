## `fastkafka.testing.LocalRedpandaBroker` {#fastkafka.testing.LocalRedpandaBroker}


LocalRedpandaBroker class, used for running unique redpanda brokers in tests to prevent topic clashing.

### `__init__` {#init}

`def __init__(self, topics: Iterable[str] = [], retries: int = 3, apply_nest_asyncio: bool = False, listener_port: int = 9092, tag: str = 'v23.1.2', seastar_core: int = 1, memory: str = '1G', mode: str = 'dev-container', default_log_level: str = 'debug', **kwargs: Dict[str, Any]) -> None`

Initialises the LocalRedpandaBroker object

**Parameters**:
- `listener_port`: Port on which the clients (producers and consumers) can connect
- `tag`: Tag of Redpanda image to use to start container
- `seastar_core`: Core(s) to use byt Seastar (the framework Redpanda uses under the hood)
- `memory`: The amount of memory to make available to Redpanda
- `mode`: Mode to use to load configuration properties in container
- `default_log_level`: Log levels to use for Redpanda

### `get_service_config_string` {#get_service_config_string}

`def get_service_config_string(self, service: str, data_dir: pathlib.Path) -> str`

Generates a configuration for a service

**Parameters**:
- `data_dir`: Path to the directory where the zookeepeer instance will save data
- `service`: "redpanda", defines which service to get config string for

### `start` {#start}

`def start(self: fastkafka.testing.LocalRedpandaBroker) -> str`

Starts a local redpanda broker instance synchronously

**Returns**:
- Redpanda broker bootstrap server address in string format: add:port

### `stop` {#stop}

`def stop(self: fastkafka.testing.LocalRedpandaBroker) -> None`

Stops a local redpanda broker instance synchronously

**Returns**:
- None

