# Context Extra options

Also, `Context` provides you some extra abilities to work with a containing object.

## Default values

As an example, if you try to access a field that does not exist in the global context, you will get the `pydantic.ValidationError` exception.

However, you can set the default value if you feel the need.

{!> includes/getting_started/context/default.md !}

## Cast context types

By default, context fields are **NOT CAST** to the type specified in their annotation.

{!> includes/getting_started/context/not_cast.md !}

If you need this functionality, you can set the appropriate flag.

{!> includes/getting_started/context/cast.md !}
