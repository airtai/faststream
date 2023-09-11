# Subscriber testing

Original application

{!> includes/getting_started/subscription/testing/1.md !}

* in-memory TestClient
* publishing (show error raising)
* check incoming message body
* note about mock clearing after context exit

{!> includes/getting_started/subscription/testing/2.md !}

* test with real broker
* wait consumer called

Show pytests setup toggle example (details in the application [config](../config/index.md){.internal-link}):

```console
REAL=True/False pytest tests
```
