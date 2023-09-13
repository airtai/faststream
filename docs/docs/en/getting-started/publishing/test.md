# Publisher Testing

If you are working with Publisher object (decorator/direct), you able to check outcoming message too

* in-memory TestClient
* publishing (show error raising)
* check incoming message body
* note about mock clearing after context exit

Base application

=== "Decorator"
    {!> includes/getting_started/publishing/testing/1.md !}

=== "Direct"
    {!> includes/getting_started/publishing/testing/2.md !}

Testing

{!> includes/getting_started/publishing/testing/3.md !}

* test with real broker
* wait consumer called
