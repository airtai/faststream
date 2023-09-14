# Custom Decoder

At this stage, the body of **StreamMessage** is transformed to the form in which it enters your handler function. This method you will have to redefine more often.

## Signature

In the original, its signature is quite simple (this is a simplified version):

{!> includes/getting_started/serialization/decoder/1.md !}

Also, you are able to reuse the original decoder function by using next signature

{!> includes/getting_started/serialization/decoder/2.md !}

!!! note
    Original decoder is always async function, so your custom one should be an async too

After you can set this decoder at broker or subsriber level both.

## Example

You can find *Protobuf* and *Msgpack* serialization examples in the [next](./examples.md){.internal-link} article.
