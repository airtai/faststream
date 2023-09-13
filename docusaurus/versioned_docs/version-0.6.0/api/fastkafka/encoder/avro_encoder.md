## `fastkafka.encoder.avro_encoder` {#fastkafka.encoder.avro_encoder}

### `avro_encoder` {#avro_encoder}

`def avro_encoder(msg: pydantic.main.BaseModel) -> bytes`

Encoder to encode pydantic instances to avro message

**Parameters**:
- `msg`: An instance of pydantic basemodel

**Returns**:
- A bytes message which is encoded from pydantic basemodel

