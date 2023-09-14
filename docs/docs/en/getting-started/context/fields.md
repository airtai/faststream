---
comment_1: This way you can get access to context object by its' name
comment_2: This way you can get access to context object specific field
---

# Access by name

Sometimes you may need to use a different name for the argument (not the one under which it is stored in the context). Or even get access not to the whole object, but only to its field or method. To do this, just specify by name what you want to get - and the context will provide you with the wished object.

{% import 'getting_started/context/fields.md' as includes with context %}
{{ includes }}
