from opentelemetry.trace import Span
from typing_extensions import Annotated

from faststream import Context

CurrentSpan = Annotated[Span, Context("span")]
