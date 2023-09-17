# Subscriber testing

Testability is a very important part of any application. And **FastStream** provides you with the tools to test your code in a easy way.

## Original application

Lets take a look at the original application to test

{!> includes/getting_started/subscription/testing/1.md !}

It consumes **JSON** messages like `#!json { "name": "username", "user_id": 1 }`

You can test your consume function like a regular one for sure:

```python
@pytest.mark.asyncio
async def test_handler():
    await handle("John", 1)
```

But if you want to test your functional closer to your real runtumi, you should use special **FastStream** test client.

## In Memory testing

Deploy a whole service with a Message Broker  is a bit too much just for testing purposes. Especially in your CI environment.
And this is not to mention the possible loss of messages due to network failures when working with real brokers.

This reason **FastStream** has a special `TestClient` to make your broker work in `InMemory` mode.

Just use it like a regular async context manager - all publishing messages will be routed in-memory (without any external dependencies) and consumed by a correct handler.

{!> includes/getting_started/subscription/testing/2.md !}

### Catching exceptions

This way you can catch any exceptions occures inside your handler

{!> includes/getting_started/subscription/testing/3.md !}

### Validates input

Also, your handler has a mock object to validate your input or call counts.

{!> includes/getting_started/subscription/testing/4.md !}

!!! note
    Handler mock has a not-serialized **JSON** message body. This way you can validate incoming message view, not python arguments.

    Thus our example checks not `#!python mock.assert_called_with(name="John", user_id=1)`, but `#!python mock.assert_called_with({ "name": "John", "user_id": 1 })`

You should be accurate with this feature: all mock objects will be cleared with the context manager exited

{!> includes/getting_started/subscription/testing/5.md !}

## Real Broker testing

If you want to test your application in a real environment, you shouldn't rewrite all you tests: just pass `with_real` optional to your `TestClient` context manager. This way `TestClient` supports all testing features, but uses not-patched broker to send and consume messages.

{!> includes/getting_started/subscription/testing/real.md !}

!!! tip
    When you using patched broker to test your consumers, publish method is calling synchronously with a consumer one, so you need no to wait until you message will be consumed. But in the real broker case it doesn't.

    This reason you have to wait a message consuming manually with the special `#!python handler.wait_call(timeout)` method.

### Little tip

It can be very helpful to set `with_real` flag by environment variable. This way you will be able to choose testing way right from the command line:

```bash
WITH_REAL=True/False pytest tests/
```

To know more about your application config management visit [this](../config/index.md){.internal-link} page.
