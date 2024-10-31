from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from fast_depends import Provider
    from fast_depends.library.serializer import SerializerProto

    from faststream._internal.basic_types import Decorator
    from faststream._internal.context import ContextRepo


@dataclass
class FastDependsData:
    use_fastdepends: bool
    get_dependent: Optional[Callable[..., Any]]
    call_decorators: Sequence["Decorator"]
    provider: "Provider"
    serializer: Optional["SerializerProto"]
    context: "ContextRepo"
