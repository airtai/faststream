from typing import TYPE_CHECKING, Any, List, Optional, cast

from opentelemetry import baggage
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from typing_extensions import Self

from faststream import context

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.types import AnyDict

_BAGGAGE_PROPAGATOR = W3CBaggagePropagator()


class Baggage:
    __slots__ = ("_baggage", "_batch_baggage")

    def __init__(self, payload: "AnyDict") -> None:
        self._baggage = dict(payload)
        self._batch_baggage: List[AnyDict] = []

    def get_all(self) -> "AnyDict":
        return self._baggage.copy()

    def get_all_batch(self) -> List["AnyDict"]:
        return self._batch_baggage.copy()

    def get(self, key: str) -> Optional[Any]:
        return self._baggage.get(key)

    def remove(self, key: str) -> None:
        self._baggage.pop(key, None)

    def set(self, key: str, value: Any) -> None:
        self._baggage[key] = value

    def propagate(self) -> None:
        context.set_local("baggage", self)

    @staticmethod
    def terminate() -> None:
        context.set_local("baggage", None)

    @classmethod
    def extract(cls, msg: "StreamMessage[Any]") -> Self:
        if not msg.batch_headers:
            payload = baggage.get_all(_BAGGAGE_PROPAGATOR.extract(msg.headers))
            return cls(cast("AnyDict", payload))

        cumulative_baggage: AnyDict = {}
        batch_baggage: List[AnyDict] = []

        for headers in msg.batch_headers:
            payload = baggage.get_all(_BAGGAGE_PROPAGATOR.extract(headers))
            cumulative_baggage.update(payload)
            batch_baggage.append(cast("AnyDict", payload))

        bag = cls(cumulative_baggage)
        bag._batch_baggage = batch_baggage
        return bag

    def __repr__(self) -> str:
        return self._baggage.__repr__()
