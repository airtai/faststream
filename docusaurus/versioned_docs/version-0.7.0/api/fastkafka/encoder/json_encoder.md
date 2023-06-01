## `fastkafka.encoder.json_encoder` {#fastkafka.encoder.json_encoder}

### `json_encoder` {#json_encoder}

`def json_encoder(msg: pydantic.main.BaseModel) -> bytes`

Encoder to encode pydantic instances to json string

**Parameters**:
- `msg`: An instance of pydantic basemodel

**Returns**:
- Json string in bytes which is encoded from pydantic basemodel

