## fastkafka.testing.ApacheKafkaBroker {#fastkafka.testing.ApacheKafkaBroker}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/apache_kafka_broker.py#L168-L305" class="link-to-source" target="_blank">View source</a>


ApacheKafkaBroker class, used for running unique kafka brokers in tests to prevent topic clashing.

### __init__ {#fastkafka._testing.apache_kafka_broker.ApacheKafkaBroker.init}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/apache_kafka_broker.py#L173-L209" class="link-to-source" target="_blank">View source</a>

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

|  Name | Type | Description | Default |
|---|---|---|---|
| `topics` | `Iterable[str]` | List of topics to create after sucessfull Kafka broker startup | `[]` |
| `retries` | `int` | Number of retries to create kafka and zookeeper services using random | `3` |
| `apply_nest_asyncio` | `bool` | set to True if running in notebook | `False` |
| `zookeeper_port` | `int` | Port for clients (Kafka brokes) to connect | `2181` |
| `listener_port` | `int` | Port on which the clients (producers and consumers) can connect | `9092` |

### get_service_config_string {#fastkafka._testing.apache_kafka_broker.ApacheKafkaBroker.get_service_config_string}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/apache_kafka_broker.py#L459-L475" class="link-to-source" target="_blank">View source</a>

```py
get_service_config_string(
    self, service, data_dir
)
```

Gets the configuration string for a service.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `service` | `str` | Name of the service ("kafka" or "zookeeper"). | *required* |
| `data_dir` | `Path` | Path to the directory where the service will save data. | *required* |

**Returns**:

|  Type | Description |
|---|---|
| `str` | The service configuration string. |

### is_started {#fastkafka._testing.apache_kafka_broker.ApacheKafkaBroker.is_started}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/apache_kafka_broker.py#L212-L222" class="link-to-source" target="_blank">View source</a>

```py
@property
is_started(
    self
)
```

Property indicating whether the ApacheKafkaBroker object is started.

The is_started property indicates if the ApacheKafkaBroker object is currently
in a started state. This implies that Zookeeper and Kafka broker processes have
sucesfully started and are ready for handling events.

**Returns**:

|  Type | Description |
|---|---|
| `bool` | True if the object is started, False otherwise. |

### start {#fastkafka._testing.apache_kafka_broker.ApacheKafkaBroker.start}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/apache_kafka_broker.py#L624-L664" class="link-to-source" target="_blank">View source</a>

```py
start(
    self
)
```

Starts a local Kafka broker and ZooKeeper instance synchronously.

**Returns**:

|  Type | Description |
|---|---|
| `str` | The Kafka broker bootstrap server address in string format: host:port. |

### stop {#fastkafka._testing.apache_kafka_broker.ApacheKafkaBroker.stop}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_testing/apache_kafka_broker.py#L668-L680" class="link-to-source" target="_blank">View source</a>

```py
stop(
    self
)
```

Stops a local kafka broker and zookeeper instance synchronously

