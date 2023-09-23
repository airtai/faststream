from typing import Any, Dict, Optional, Union

from faststream.nats.js_stream import JsStream


class StreamBuilder:
    streams: Dict[str, JsStream]

    def __init__(self):
        self.streams = {}

    def stream(
        self,
        name: Union[str, JsStream, None],
        *args: Any,
        declare: bool = True,
        **kwargs: Any,
    ) -> Optional[JsStream]:
        stream = JsStream.validate(name)

        if stream is not None:
            stream = self.streams[stream.name] = self.streams.get(stream.name, stream)

        return stream


stream_builder = StreamBuilder()
