### avro_encoder {#fastkafka.encoder.avro_encoder}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/encoder/avro.py#L239-L259" class="link-to-source" target="_blank">View source</a>

```py
avro_encoder(
    msg
)
```

Encoder to encode pydantic instances to avro message

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `msg` | `BaseModel` | An instance of pydantic basemodel | *required* |

**Returns**:

|  Type | Description |
|---|---|
| `bytes` | A bytes message which is encoded from pydantic basemodel |

