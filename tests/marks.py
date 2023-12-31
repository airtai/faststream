import sys

import pytest

from faststream._compat import PYDANTIC_V2

python39 = pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9+")

python310 = pytest.mark.skipif(
    sys.version_info < (3, 10), reason="requires python3.10+"
)

pydanticV1 = pytest.mark.skipif(PYDANTIC_V2, reason="requires PydanticV2")  # noqa: N816

pydanticV2 = pytest.mark.skipif(not PYDANTIC_V2, reason="requires PydanticV1")  # noqa: N816
