---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Publisher Testing

If you are working with a Publisher object (either as a decorator or directly), you have several testing features available:

* In-memory TestClient
* Publishing locally with error propagation
* Checking the incoming message body

## Base Application

Let's take a look at a simple application example with a publisher as a decorator or as a direct call:

=== "Decorator"
    {!> includes/getting_started/publishing/testing/1.md !}

=== "Direct"
    {!> includes/getting_started/publishing/testing/2.md !}

## Testing

To test it, you just need to patch your broker with a special *TestBroker*.

{! includes/getting_started/publishing/testing/3.md !}

By default, it patches your broker to run **In-Memory**, so you can use it without any external broker. It should be extremely useful in your CI or local development environment.

Also, it allows you to check the outgoing message body in the same way as with a [subscriber](../subscription/test.md#validates-input){.internal-link}.

```python
publisher.mock.assert_called_once_with("Hi!")
```

!!! note
    The Publisher mock contains not just a `publish` method input value. It sets up a virtual consumer for an outgoing topic, consumes a message, and stores this consumed one.

Additionally, *TestBroker* can be used with a real external broker to make your tests end-to-end suitable. For more information, please visit the [subscriber testing page](../subscription/test.md#real-broker-testing){.internal-link}.
