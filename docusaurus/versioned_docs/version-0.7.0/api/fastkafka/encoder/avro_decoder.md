## `fastkafka.encoder.avro_decoder` {#fastkafka.encoder.avro_decoder}

### `avro_decoder` {#avro_decoder}

`def avro_decoder(raw_msg: bytes, cls: pydantic.main.ModelMetaclass) -> Any`

Decoder to decode avro encoded messages to pydantic model instance

**Parameters**:
- `raw_msg`: Avro encoded bytes message received from Kafka topic
- `cls`: Pydantic class; This pydantic class will be used to construct instance of same class

**Returns**:
- An instance of given pydantic class

