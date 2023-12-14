---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Context Extra Options

Additionally, `Context` provides you with some extra capabilities for working with containing objects.

## Default Values

For instance, if you attempt to access a field that doesn't exist in the global context, you will receive a `pydantic.ValidationError` exception.

However, you can set default values if needed.

{! includes/getting_started/context/default.md !}

## Cast Context Types

By default, context fields are **NOT CAST** to the type specified in their annotation.

{! includes/getting_started/context/not_cast.md !}

If you require this functionality, you can enable the appropriate flag.

{! includes/getting_started/context/cast.md !}
