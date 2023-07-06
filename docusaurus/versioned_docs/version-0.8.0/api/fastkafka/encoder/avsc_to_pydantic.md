### avsc_to_pydantic {#fastkafka.encoder.avsc_to_pydantic}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/encoder/avro.py#L283-L403" class="link-to-source" target="_blank">View source</a>

```py
avsc_to_pydantic(
    schema
)
```

Generate pydantic model from given Avro Schema

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `schema` | `Dict[str, Any]` | Avro schema in dictionary format | *required* |

**Returns**:

|  Type | Description |
|---|---|
| `Type[pydantic.main.BaseModel]` | Pydantic model class built from given avro schema |

