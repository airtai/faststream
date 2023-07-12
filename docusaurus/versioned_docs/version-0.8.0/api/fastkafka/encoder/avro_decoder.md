### avro_decoder {#fastkafka.encoder.avro_decoder}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/encoder/avro.py#L263-L279" class="link-to-source" target="_blank">View source</a>

```py
avro_decoder(
    raw_msg, cls
)
```

Decoder to decode avro encoded messages to pydantic model instance

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `raw_msg` | `bytes` | Avro encoded bytes message received from Kafka topic | *required* |
| `cls` | `Type[pydantic.main.BaseModel]` | Pydantic class; This pydantic class will be used to construct instance of same class | *required* |

**Returns**:

|  Type | Description |
|---|---|
| `Any` | An instance of given pydantic class |

