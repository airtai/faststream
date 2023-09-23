import pytest

from faststream._compat import PYDANTIC_V2

pydanticV1 = pytest.mark.skipif(PYDANTIC_V2, reason="requires PydanticV2")
