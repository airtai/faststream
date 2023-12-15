---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Application-level Filtering

**FastStream** also allows you to specify the message processing way using message headers, body type or something else. The `filter` feature enables you to consume various messages with different schemas within a single event stream.

!!! tip
    Message must be consumed at ONCE (crossing filters are not allowed)

As an example, let's create a subscriber for both `JSON` and non-`JSON` messages:

{! includes/getting_started/subscription/filtering/1.md !}

!!! note
    A subscriber without a filter is a default subscriber. It consumes messages that have not been consumed yet.

For now, the following message will be delivered to the `handle` function

{! includes/getting_started/subscription/filtering/2.md !}

And this one will be delivered to the `default_handler`

{! includes/getting_started/subscription/filtering/3.md !}
