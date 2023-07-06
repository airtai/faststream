## `fastkafka.encoder.json_decoder` {#fastkafka.encoder.json_decoder}

### `json_decoder` {#json_decoder}

`def json_decoder(raw_msg: bytes, cls: pydantic.main.ModelMetaclass) -> Any`

Decoder to decode json string in bytes to pydantic model instance

**Parameters**:
- `raw_msg`: Bytes message received from Kafka topic
- `cls`: Pydantic class; This pydantic class will be used to construct instance of same class

**Returns**:
- An instance of given pydantic class

