---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Subscriber Testing

Testability is a crucial part of any application, and **FastStream** provides you with the tools to test your code easily.

## Original Application

Let's take a look at the original application to test

{! includes/getting_started/subscription/testing/1.md !}

It consumes **JSON** messages like `#!json { "name": "username", "user_id": 1 }`

You can test your consume function like a regular one, for sure:

```python
@pytest.mark.asyncio
async def test_handler():
    await handle("John", 1)
```

But if you want to test your function closer to your real runtime, you should use the special **FastStream** test client.

## In-Memory Testing

Deploying a whole service with a Message Broker is a bit too much just for testing purposes, especially in your CI environment. Not to mention the possible loss of messages due to network failures when working with real brokers.

For this reason, **FastStream** has a special `TestClient` to make your broker work in `InMemory` mode.

Just use it like a regular async context manager - all published messages will be routed in-memory (without any external dependencies) and consumed by the correct handler.

{! includes/getting_started/subscription/testing/2.md !}

### Catching Exceptions

This way you can catch any exceptions that occur inside your handler:

{! includes/getting_started/subscription/testing/3.md !}

### Validates Input

Also, your handler has a mock object to validate your input or call counts.

{! includes/getting_started/subscription/testing/4.md !}

!!! note
    The Handler mock has a not-serialized **JSON** message body. This way you can validate the incoming message view, not python arguments.

    Thus our example checks not `#!python mock.assert_called_with(name="John", user_id=1)`, but `#!python mock.assert_called_with({ "name": "John", "user_id": 1 })`.

You should be careful with this feature: all mock objects will be cleared when the context manager exits.

{! includes/getting_started/subscription/testing/5.md !}

## Real Broker Testing

If you want to test your application in a real environment, you shouldn't have to rewrite all your tests: just pass `with_real` optional parameter to your `TestClient` context manager. This way, `TestClient` supports all the testing features but uses an unpatched broker to send and consume messages.

{! includes/getting_started/subscription/testing/real.md !}

!!! tip
    When you're using a patched broker to test your consumers, the publish method is called synchronously with a consumer one, so you need not wait until your message is consumed. But in the real broker's case, it doesn't.

    For this reason, you have to wait for message consumption manually with the special `#!python handler.wait_call(timeout)` method.
    Also, inner handler exceptions will be raised in this function, not `#!python broker.publish(...)`.

### A Little Tip

It can be very helpful to set the `with_real` flag using an environment variable. This way, you will be able to choose the testing mode right from the command line:

```bash
WITH_REAL=True/False pytest ...
```

To learn more about managing your application configuration visit [this page](../config/index.md){.internal-link}.
