---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Pydantic Serialization

## pydantic.Field

Besides, **FastStream** uses your handlers' annotations to collect information about the application schema and generate [**AsyncAPI**](https://www.asyncapi.com){.external-link target="_blank"} schema.

You can access this information with extra details using `pydantic.Field` (such as title, description and examples). Additionally, [**Fields**](https://docs.pydantic.dev/latest/usage/fields/){.external-link target="_blank"} usage allows you to add extra validations to your message schema.

Just use `pydantic.Field` as a function default argument:

{! includes/getting_started/subscription/pydantic/1.md !}


!!! tip
    Also you can use `typing.Annotated` (python 3.9+) or `typing_extensions.Annotated` to declare your handler fields

    ```python
    {!> docs_src/getting_started/subscription/kafka/pydantic_annotated_fields.py [ln:14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5] !}
    ```

## pydantic.BaseModel

To make your message schema reusable between different subscribers and publishers, you can declare it as a `pydantic.BaseModel` and use it as a single message annotation:

{! includes/getting_started/subscription/pydantic/2.md !}
