# Pydantic Serialization

## pydantic.Field

Besides, **FastStream** uses your handlers' annotations to collect information about apllication schema and generate [**AsyncAPI**](https://www.asyncapi.com){.external-link target="_blank"} schema.

You may reach this information by extra details using `pydantic.Field` (like title, description and examples). Also [Fields](https://docs.pydantic.dev/latest/usage/fields/){.external-link target="_blank"} usage allows you to add some extra validations to your message schema.

Just use `pydantic.Field` as a function default argument

{!> includes/getting_started/subscription/pydantic/1.md !}

## pydantic.BaseModel

To make your message schema reusable between different subscribers and publishers you can decalre it as a `pydantic.BaseModel` and use as a single message annotation

{!> includes/getting_started/subscription/pydantic/2.md !}
