## fastkafka.encoder.AvroBase {#fastkafka.encoder.AvroBase}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/encoder/avro.py#L22-L235" class="link-to-source" target="_blank">View source</a>


This is base pydantic class that will add some methods

### __init__ {#pydantic.main.BaseModel.init}



```py
__init__(
    __pydantic_self__, data
)
```

Create a new model by parsing and validating input data from keyword arguments.

Raises ValidationError if the input data cannot be parsed to form a valid model.

Uses `__pydantic_self__` instead of the more common `self` for the first arg to
allow `self` as a field name.

### avro_schema {#fastkafka._components.encoder.avro.AvroBase.avro_schema}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/encoder/avro.py#L80-L99" class="link-to-source" target="_blank">View source</a>

```py
@classmethod
avro_schema(
    by_alias=True, namespace=None
)
```

Returns the Avro schema for the Pydantic class.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `by_alias` | `bool` | Generate schemas using aliases defined. Defaults to True. | `True` |
| `namespace` | `Optional[str]` | Optional namespace string for schema generation. | `None` |

**Returns**:

|  Type | Description |
|---|---|
| `Dict[str, Any]` | The Avro schema for the model. |

### avro_schema_for_pydantic_class {#fastkafka._components.encoder.avro.AvroBase.avro_schema_for_pydantic_class}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/encoder/avro.py#L53-L77" class="link-to-source" target="_blank">View source</a>

```py
@classmethod
avro_schema_for_pydantic_class(
    pydantic_model, by_alias=True, namespace=None
)
```

Returns the Avro schema for the given Pydantic class.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `pydantic_model` | `Type[pydantic.main.BaseModel]` | The Pydantic class. | *required* |
| `by_alias` | `bool` | Generate schemas using aliases defined. Defaults to True. | `True` |
| `namespace` | `Optional[str]` | Optional namespace string for schema generation. | `None` |

**Returns**:

|  Type | Description |
|---|---|
| `Dict[str, Any]` | The Avro schema for the model. |

### avro_schema_for_pydantic_object {#fastkafka._components.encoder.avro.AvroBase.avro_schema_for_pydantic_object}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/encoder/avro.py#L26-L50" class="link-to-source" target="_blank">View source</a>

```py
@classmethod
avro_schema_for_pydantic_object(
    pydantic_model, by_alias=True, namespace=None
)
```

Returns the Avro schema for the given Pydantic object.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `pydantic_model` | `BaseModel` | The Pydantic object. | *required* |
| `by_alias` | `bool` | Generate schemas using aliases defined. Defaults to True. | `True` |
| `namespace` | `Optional[str]` | Optional namespace string for schema generation. | `None` |

**Returns**:

|  Type | Description |
|---|---|
| `Dict[str, Any]` | The Avro schema for the model. |

### copy {#pydantic.main.BaseModel.copy}



```py
copy(
    self, include=None, exclude=None, update=None, deep=False
)
```

Returns a copy of the model.

This method is now deprecated; use `model_copy` instead. If you need `include` or `exclude`, use:

```py
data = self.model_dump(include=include, exclude=exclude, round_trip=True)
data = {**data, **(update or {})}
copied = self.model_validate(data)
```

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `include` | AbstractSetIntStr | MappingIntStrAny | None | Optional set or mappingspecifying which fields to include in the copied model. | `None` |
| `exclude` | AbstractSetIntStr | MappingIntStrAny | None | Optional set or mappingspecifying which fields to exclude in the copied model. | `None` |
| `update` | `Dict[str, Any] | None` | Optional dictionary of field-value pairs to override field valuesin the copied model. | `None` |
| `deep` | bool | If True, the values of fields that are Pydantic models will be deep copied. | `False` |

**Returns**:

|  Type | Description |
|---|---|
| `Model` | A copy of the model with included, excluded and updated fields as specified. |

### model_computed_fields {#pydantic.main.BaseModel.model_computed_fields}



```py
@property
model_computed_fields(
    self
)
```

Get the computed fields of this model instance.

**Returns**:

|  Type | Description |
|---|---|
| `dict[str, ComputedFieldInfo]` | A dictionary of computed field names and their corresponding `ComputedFieldInfo` objects. |

### model_construct {#pydantic.main.BaseModel.model_construct}



```py
@classmethod
model_construct(
    _fields_set=None, values
)
```

Creates a new instance of the `Model` class with validated data.

Creates a new model setting `__dict__` and `__pydantic_fields_set__` from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `_fields_set` | set[str] | None | The set of field names accepted for the Model instance. | `None` |
| `values` | Any | Trusted or pre-validated data dictionary. | *required* |

**Returns**:

|  Type | Description |
|---|---|
| `Model` | A new instance of the `Model` class with validated data. |

### model_copy {#pydantic.main.BaseModel.model_copy}



```py
model_copy(
    self, update=None, deep=False
)
```

Returns a copy of the model.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `update` | dict[str, Any] | None | Values to change/add in the new model. Note: the data is not validatedbefore creating the new model. You should trust this data. | `None` |
| `deep` | bool | Set to `True` to make a deep copy of the model. | `False` |

**Returns**:

|  Type | Description |
|---|---|
| `Model` | New model instance. |

### model_dump {#pydantic.main.BaseModel.model_dump}



```py
model_dump(
    self,
    mode='python',
    include=None,
    exclude=None,
    by_alias=False,
    exclude_unset=False,
    exclude_defaults=False,
    exclude_none=False,
    round_trip=False,
    warnings=True,
)
```

Usage docs: https://docs.pydantic.dev/dev-v2/usage/serialization/#modelmodel_dump

Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `mode` | Literal['json', 'python'] | str | The mode in which `to_python` should run.If mode is 'json', the dictionary will only contain JSON serializable types.If mode is 'python', the dictionary may contain any Python objects. | `'python'` |
| `include` | IncEx | A list of fields to include in the output. | `None` |
| `exclude` | IncEx | A list of fields to exclude from the output. | `None` |
| `by_alias` | bool | Whether to use the field's alias in the dictionary key if defined. | `False` |
| `exclude_unset` | bool | Whether to exclude fields that are unset or None from the output. | `False` |
| `exclude_defaults` | bool | Whether to exclude fields that are set to their default value from the output. | `False` |
| `exclude_none` | bool | Whether to exclude fields that have a value of `None` from the output. | `False` |
| `round_trip` | bool | Whether to enable serialization and deserialization round-trip support. | `False` |
| `warnings` | bool | Whether to log warnings when invalid fields are encountered. | `True` |

**Returns**:

|  Type | Description |
|---|---|
| `dict[str, Any]` | A dictionary representation of the model. |

### model_dump_json {#pydantic.main.BaseModel.model_dump_json}



```py
model_dump_json(
    self,
    indent=None,
    include=None,
    exclude=None,
    by_alias=False,
    exclude_unset=False,
    exclude_defaults=False,
    exclude_none=False,
    round_trip=False,
    warnings=True,
)
```

Usage docs: https://docs.pydantic.dev/dev-v2/usage/serialization/#modelmodel_dump_json

Generates a JSON representation of the model using Pydantic's `to_json` method.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `indent` | int | None | Indentation to use in the JSON output. If None is passed, the output will be compact. | `None` |
| `include` | IncEx | Field(s) to include in the JSON output. Can take either a string or set of strings. | `None` |
| `exclude` | IncEx | Field(s) to exclude from the JSON output. Can take either a string or set of strings. | `None` |
| `by_alias` | bool | Whether to serialize using field aliases. | `False` |
| `exclude_unset` | bool | Whether to exclude fields that have not been explicitly set. | `False` |
| `exclude_defaults` | bool | Whether to exclude fields that have the default value. | `False` |
| `exclude_none` | bool | Whether to exclude fields that have a value of `None`. | `False` |
| `round_trip` | bool | Whether to use serialization/deserialization between JSON and class instance. | `False` |
| `warnings` | bool | Whether to show any warnings that occurred during serialization. | `True` |

**Returns**:

|  Type | Description |
|---|---|
| `str` | A JSON string representation of the model. |

### model_extra {#pydantic.main.BaseModel.model_extra}



```py
@property
model_extra(
    self
)
```

Get extra fields set during validation.

**Returns**:

|  Type | Description |
|---|---|
| `dict[str, Any] | None` | A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. |

### model_fields_set {#pydantic.main.BaseModel.model_fields_set}



```py
@property
model_fields_set(
    self
)
```

Returns the set of fields that have been set on this model instance.

**Returns**:

|  Type | Description |
|---|---|
| `set[str]` | A set of strings representing the fields that have been set,i.e. that were not filled from defaults. |

### model_json_schema {#pydantic.main.BaseModel.model_json_schema}



```py
@classmethod
model_json_schema(
    by_alias=True,
    ref_template='#/$defs/{model}',
    schema_generator=<class 'pydantic.json_schema.GenerateJsonSchema'>,
    mode='validation',
)
```

Generates a JSON schema for a model class.

To override the logic used to generate the JSON schema, you can create a subclass of `GenerateJsonSchema`
with your desired modifications, then override this method on a custom base class and set the default
value of `schema_generator` to be your subclass.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `by_alias` | bool | Whether to use attribute aliases or not. | `True` |
| `ref_template` | str | The reference template. | `'#/$defs/{model}'` |
| `schema_generator` | type[GenerateJsonSchema] | The JSON schema generator. | `<class 'pydantic.json_schema.GenerateJsonSchema'>` |
| `mode` | JsonSchemaMode | The mode in which to generate the schema. | `'validation'` |

**Returns**:

|  Type | Description |
|---|---|
| `dict[str, Any]` | The JSON schema for the given model class. |

### model_parametrized_name {#pydantic.main.BaseModel.model_parametrized_name}



```py
@classmethod
model_parametrized_name(
    params
)
```

Compute the class name for parametrizations of generic classes.

This method can be overridden to achieve a custom naming scheme for generic BaseModels.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `params` | tuple[type[Any], ...] | Tuple of types of the class. Given a generic class`Model` with 2 type variables and a concrete model `Model[str, int]`,the value `(str, int)` would be passed to `params`. | *required* |

**Returns**:

|  Type | Description |
|---|---|
| `str` | String representing the new class where `params` are passed to `cls` as type variables. |

**Exceptions**:

|  Type | Description |
|---|---|
| `TypeError` | Raised when trying to generate concrete names for non-generic models. |

### model_post_init {#pydantic.main.BaseModel.model_post_init}



```py
model_post_init(
    self, _BaseModel__context
)
```

Override this method to perform additional initialization after `__init__` and `model_construct`.

This is useful if you want to do some validation that requires the entire model to be initialized.

### model_rebuild {#pydantic.main.BaseModel.model_rebuild}



```py
@classmethod
model_rebuild(
    force=False,
    raise_errors=True,
    _parent_namespace_depth=2,
    _types_namespace=None,
)
```

Try to rebuild the pydantic-core schema for the model.

This may be necessary when one of the annotations is a ForwardRef which could not be resolved during
the initial attempt to build the schema, and automatic rebuilding fails.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `force` | bool | Whether to force the rebuilding of the model schema, defaults to `False`. | `False` |
| `raise_errors` | bool | Whether to raise errors, defaults to `True`. | `True` |
| `_parent_namespace_depth` | int | The depth level of the parent namespace, defaults to 2. | `2` |
| `_types_namespace` | dict[str, Any] | None | The types namespace, defaults to `None`. | `None` |

**Returns**:

|  Type | Description |
|---|---|
| `bool | None` | Returns `None` if the schema is already "complete" and rebuilding was not required.If rebuilding _was_ required, returns `True` if rebuilding was successful, otherwise `False`. |

### model_validate {#pydantic.main.BaseModel.model_validate}



```py
@classmethod
model_validate(
    obj, strict=None, from_attributes=None, context=None
)
```

Validate a pydantic model instance.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `obj` | Any | The object to validate. | *required* |
| `strict` | bool | None | Whether to raise an exception on invalid fields. | `None` |
| `from_attributes` | bool | None | Whether to extract data from object attributes. | `None` |
| `context` | dict[str, Any] | None | Additional context to pass to the validator. | `None` |

**Returns**:

|  Type | Description |
|---|---|
| `Model` | The validated model instance. |

**Exceptions**:

|  Type | Description |
|---|---|
| `ValidationError` | If the object could not be validated. |

### model_validate_json {#pydantic.main.BaseModel.model_validate_json}



```py
@classmethod
model_validate_json(
    json_data, strict=None, context=None
)
```

Validate the given JSON data against the Pydantic model.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `json_data` | str | bytes | bytearray | The JSON data to validate. | *required* |
| `strict` | bool | None | Whether to enforce types strictly. | `None` |
| `context` | dict[str, Any] | None | Extra variables to pass to the validator. | `None` |

**Returns**:

|  Type | Description |
|---|---|
| `Model` | The validated Pydantic model. |

**Exceptions**:

|  Type | Description |
|---|---|
| `ValueError` | If `json_data` is not a JSON string. |

