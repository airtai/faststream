from typing import Dict, Optional, Union

from faststream.nats.schemas.js_stream import JStream


class StreamBuilder:
    """A class to build streams."""

    streams: Dict[str, JStream]

    def __init__(self) -> None:
        """Initialize the stream builder."""
        self.streams = {}

    def stream(
        self,
        name: Union[str, JStream, None],
    ) -> Optional[JStream]:
        """Get a stream.

        Args:
            *args: The arguments.
            name: The stream name.
            declare: Whether to declare the stream.
            **kwargs: The keyword arguments.
        """
        stream = JStream.validate(name)

        if stream is not None:
            stream = self.streams[stream.name] = self.streams.get(stream.name, stream)

        return stream


stream_builder = StreamBuilder()
