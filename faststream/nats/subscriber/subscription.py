from typing import Generic, Protocol, TypeVar


class Unsubscriptable(Protocol):
    async def unsubscribe(self) -> None: ...


class Stopable(Protocol):
    async def stop(self) -> None: ...


StopableT = TypeVar("StopableT", bound=Stopable)


class UnsubscribeAdapter(Unsubscriptable, Generic[StopableT]):
    __slots__ = ("obj",)

    obj: StopableT

    def __init__(self, subscription: StopableT):
        self.obj = subscription

    async def unsubscribe(self) -> None:
        await self.obj.stop()
