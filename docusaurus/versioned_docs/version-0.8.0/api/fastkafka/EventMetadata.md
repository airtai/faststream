## fastkafka.EventMetadata {#fastkafka.EventMetadata}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/aiokafka_consumer_loop.py#L27-L77" class="link-to-source" target="_blank">View source</a>


A class for encapsulating Kafka record metadata.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `topic` | `str` | The topic this record is received from | *required* |
| `partition` | `int` | The partition from which this record is received | *required* |
| `offset` | `int` | The position of this record in the corresponding Kafka partition | *required* |
| `timestamp` | `int` | The timestamp of this record | *required* |
| `timestamp_type` | `int` | The timestamp type of this record | *required* |
| `key` | `Optional[bytes]` | The key (or `None` if no key is specified) | *required* |
| `value` | `Optional[bytes]` | The value | *required* |
| `serialized_key_size` | `int` | The size of the serialized, uncompressed key in bytes | *required* |
| `serialized_value_size` | `int` | The size of the serialized, uncompressed value in bytes | *required* |
| `headers` | `Sequence[Tuple[str, bytes]]` | The headers | *required* |

### create_event_metadata {#fastkafka._components.aiokafka_consumer_loop.EventMetadata.create_event_metadata}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/aiokafka_consumer_loop.py#L56-L77" class="link-to-source" target="_blank">View source</a>

```py
@staticmethod
create_event_metadata(
    record
)
```

Creates an instance of EventMetadata from a ConsumerRecord.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `record` | `ConsumerRecord` | The Kafka ConsumerRecord. | *required* |

**Returns**:

|  Type | Description |
|---|---|
| `EventMetadata` | The created EventMetadata instance. |

