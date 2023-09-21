# Publisher Testing

If you are working with a Publisher object (either decorator or direct), you can check outgoing messages as well. There are several testing features available:

* In-memory TestClient
* Publishing (including error handling)
* Checking the incoming message body
* Note about mock clearing after the context exits

## Base application

=== "Decorator"
    {!> includes/getting_started/publishing/testing/1.md !}

=== "Direct"
    {!> includes/getting_started/publishing/testing/2.md !}

## Testing

{!> includes/getting_started/publishing/testing/3.md !}

* Testing with a real broker
* Waiting for the consumer to be called
