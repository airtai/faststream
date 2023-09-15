# Application-level filtering

Also, **FastStream** allows you to specify message processing way by message headers, body type or smth else. Using `filter` feature you are able to consume various messages with different schemas in the one event stream.

!!! tip
    Message must be consumed at ONCE (crossing filters are not allowed)

As an example lets create a subscriber for `JSON` and not-`JSON` messages both:

{!> includes/getting_started/subscription/filtering/1.md !}

!!! note
    Subscriber without filter is a default subscriber. It consumes messages, not consumed yet.


For now, the following message will be delivered to the `handle` function

{!> includes/getting_started/subscription/filtering/2.md !}

And this one will be delivered to the `default_handler`

{!> includes/getting_started/subscription/filtering/3.md !}
