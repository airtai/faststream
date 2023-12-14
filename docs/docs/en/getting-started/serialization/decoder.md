---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Custom Decoder

At this stage, the body of a **StreamMessage** is transformed into the format that it will take when it enters your handler function. This stage is the one you will need to redefine more often.

## Signature

The original decoder function has a relatively simple signature (this is a simplified version):

{! includes/getting_started/serialization/decoder/1.md !}

Alternatively, you can reuse the original decoder function with the following signature:

{! includes/getting_started/serialization/decoder/2.md !}

!!! note
    The original decoder is always an asynchronous function, so your custom decoder should also be asynchronous.

Afterward, you can set this custom decoder at the broker or subscriber level.

## Example

You can find examples of *Protobuf*, *Msgpack* and *Avro* serialization in the [next article](./examples.md){.internal-link}.
