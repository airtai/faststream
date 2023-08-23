import sys

import pytest

needs_py310 = pytest.mark.skipif(
    sys.version_info < (3, 10), reason="requires python3.10+"
)

needs_py38 = pytest.mark.skipif(sys.version_info < (3, 8), reason="requires python3.8+")

needs_ex_py37 = pytest.mark.skipif(
    sys.version_info == (3, 8), reason="requires python3.7"
)
