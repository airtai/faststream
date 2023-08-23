import asyncio
from uuid import uuid4

import pytest


@pytest.fixture
def queue():
    return str(uuid4())


@pytest.fixture
def event():
    return asyncio.Event()
