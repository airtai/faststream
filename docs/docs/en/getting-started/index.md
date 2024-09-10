---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
hide:
  - toc
run_docker: To start a new project, we need a test broker container
---

# QUICK START

Install using `pip`:

{% import 'getting_started/index/install.md' as includes with context %}
{{ includes }}

## Basic Usage

!!! note
    Before continuing with the next steps, make sure you install *Fastream* CLI.
    ```shell
    pip install "faststream[cli]"
    ```

To create a basic application, add the following code to a new file (e.g. `serve.py`):

{! includes/getting_started/index/base.md !}

And just run this command:

```shell
faststream run serve:app
```

After running the command, you should see the following output:

```{.shell .no-copy}
INFO     - FastStream app starting...
INFO     - test |            - `BaseHandler` waiting for messages
INFO     - FastStream app started successfully! To exit, press CTRL+C
```
{ data-search-exclude }

Enjoy your new development experience!

### Manual run

Also, you can run the `FastStream` application manually, as a regular async function:

```python
import asyncio

async def main():
    app = FastStream(...)
    await app.run()  # blocking method

if __name__ == "__main__":
    asyncio.run(main())
```

### Other tools integrations

If you want to use **FastStream** as part of another framework service, you probably don't need to utilize the `FastStream` object at all, as it is primarily intended as a **CLI** tool target. Instead, you can start and stop your broker as part of another framework's lifespan. You can find such examples in the [integrations section](./integrations/frameworks/index.md){.internal-link}.

??? tip "Don't forget to stop the test broker container"
    ```bash
    docker container stop test-mq
    ```
