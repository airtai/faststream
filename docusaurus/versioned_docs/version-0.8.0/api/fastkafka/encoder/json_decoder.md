### json_decoder {#fastkafka.encoder.json_decoder}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/encoder/json.py#L42-L55" class="link-to-source" target="_blank">View source</a>

```py
json_decoder(
    raw_msg, cls
)
```

Decoder to decode json string in bytes to pydantic model instance

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `raw_msg` | `bytes` | Bytes message received from Kafka topic | *required* |
| `cls` | `Type[pydantic.main.BaseModel]` | Pydantic class; This pydantic class will be used to construct instance of same class | *required* |

**Returns**:

|  Type | Description |
|---|---|
| `Any` | An instance of given pydantic class |

