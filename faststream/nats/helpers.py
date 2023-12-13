from typing import Any, Dict, Optional, Union

from faststream.nats.js_stream import JStream


class StreamBuilder:
    streams: Dict[str, JStream]

    def __init__(self) -> None:
        self.streams = {}

    def stream(
        self,
        name: Union[str, JStream, None],
        *args: Any,
        declare: bool = True,
        **kwargs: Any,
    ) -> Optional[JStream]:
        stream = JStream.validate(name)

        if stream is not None:
            stream = self.streams[stream.name] = self.streams.get(stream.name, stream)

        return stream


stream_builder = StreamBuilder()
