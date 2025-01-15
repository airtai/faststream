from dataclasses import dataclass
from typing import Optional


@dataclass
class AsyncAPIOptions:
    title_: Optional[str]
    description_: Optional[str]
    include_in_schema: bool
