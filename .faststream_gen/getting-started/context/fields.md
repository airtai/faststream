---
comment_1: This way you can get access to context object by its name
comment_2: This way you can get access to context object specific field
---

# Access by Name

Sometimes, you may need to use a different name for the argument (not the one under which it is stored in the context) or get access to specific parts of the object. To do this, simply specify the name of what you want to access, and the context will provide you with the object.

{% import 'getting_started/context/fields.md' as includes with context %}
{{ includes }}
