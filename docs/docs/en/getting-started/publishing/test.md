# Publisher Testing

If you are working with a Publisher object (either decorator or direct), you have a several testing features available:

* In-memory TestClient
* Publishing locally with errors propogation
* Checking the incoming message body

## Base application

Lets take a look at the simple application example with publisher as a decorator/manuall call:

=== "Decorator"
    {!> includes/getting_started/publishing/testing/1.md !}

=== "Direct"
    {!> includes/getting_started/publishing/testing/2.md !}

## Testing

To test it you just need to patch your broker by special *TestBroker*

{!> includes/getting_started/publishing/testing/3.md !}

By default, it patches you broker to run **In-Memory**, so you can use it without any external broker. It should be extremely usefull in your CI or local development environment.

Also, it allows you to check outgoing message body the same way with a [subscriber](../subscription/test.md#validates-input){.internal-link}

```python
publisher.mock.assert_called_once_with("Hi!")
```

!!! note
    Publisher mock contains not just a `publish` method input value. It setups a virtual consumer for an outgoing topic, consumes a message and store this consumed one.

Also, *TestBroker* can be used with the real external broker to make you tests end-to-end suitable. To find more information, please visit [subscriber testing page](../subscription/test.md#real-broker-testing){.internal-link}
