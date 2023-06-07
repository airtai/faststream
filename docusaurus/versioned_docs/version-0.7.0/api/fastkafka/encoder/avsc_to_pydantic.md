## `fastkafka.encoder.avsc_to_pydantic` {#fastkafka.encoder.avsc_to_pydantic}

### `avsc_to_pydantic` {#avsc_to_pydantic}

`def avsc_to_pydantic(schema: Dict[str, Any]) -> ModelMetaclass`

Generate pydantic model from given Avro Schema

**Parameters**:
- `schema`: Avro schema in dictionary format

**Returns**:
- Pydantic model class built from given avro schema

