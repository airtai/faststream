---
# template variables
fastapi_plugin: If you want to use **FastStream** in conjunction with **FastAPI**, perhaps you should use a special [plugin](../fastapi/index.md){.internal-link}
no_hook: However, even if such a hook is not provided, you can do it yourself.
---

# INTEGRATIONS

**FastStream** brokers are very easy to integrate with any of your applications:
it is enough to initialize the broker at startup and close it correctly at the end of
your application.

Most HTTP frameworks have built-in lifecycle hooks for this.

{% import 'getting_started/integrations/http/1.md' as includes with context %}
{{ includes }}
