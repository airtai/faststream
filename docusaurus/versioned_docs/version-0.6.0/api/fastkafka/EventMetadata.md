## `fastkafka.EventMetadata` {#fastkafka.EventMetadata}


A class for encapsulating Kafka record metadata.

**Parameters**:
- `topic`: The topic this record is received from
- `partition`: The partition from which this record is received
- `offset`: The position of this record in the corresponding Kafka partition
- `timestamp`: The timestamp of this record
- `timestamp_type`: The timestamp type of this record
- `key`: The key (or `None` if no key is specified)
- `value`: The value
- `serialized_key_size`: The size of the serialized, uncompressed key in bytes
- `serialized_value_size`: The size of the serialized, uncompressed value in bytes
- `headers`: The headers

