# Custom Parser

At this stage, **FastStream** serializes an incoming message from the broker's framework into a general format called **StreamMessage**. During this stage, the message body remains in the form of raw bytes.

**StreamMessage** is a general representation of a message within **FastStream**. It contains all the information required for message processing within **FastStreams**.  It is even used to represent message batches, so the primary reason to customize it is to redefine the metadata associated with **FastStream** messages.

For example, you can specify your own header with the `message_id` semantic. This allows you to inform **FastStream** about this custom header through parser customization.

## Signature

To create a custom message parser, you should write a regular Python function (synchronous or asynchronous) with the following signature:

{!> includes/getting_started/serialization/parser/1.md !}

Alternatively, you can reuse the original parser function with the following signature:

{!> includes/getting_started/serialization/parser/2.md !}

The argument naming doesn't matter; the parser will always be placed as the second argument.

!!! note
    The original parser is always an asynchronous function, so your custom parser should also be asynchronous.

Afterward, you can set this custom parser at the broker or subscriber level.

## Example

As an example, let's redefine `message_id` to a custom header:

{!> includes/getting_started/serialization/parser/3.md !}
