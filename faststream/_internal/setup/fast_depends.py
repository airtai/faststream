from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Optional, Sequence

if TYPE_CHECKING:
    from faststream._internal.basic_types import Decorator


@dataclass
class FastDependsData:
    apply_types: bool
    is_validate: bool
    get_dependent: Optional[Callable[..., Any]]
    call_decorators: Sequence["Decorator"]
