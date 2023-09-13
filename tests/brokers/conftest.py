from uuid import uuid4

import pytest


@pytest.fixture
def queue():
    return str(uuid4())
