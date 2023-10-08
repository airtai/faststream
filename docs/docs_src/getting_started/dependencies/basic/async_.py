import asyncio
import pytest
from faststream import Depends, apply_types

async def simple_dependency(a: int, b: int = 3):
    return a + b

def another_dependency(a: int):
    return a

@apply_types
async def method(
    a: int,
    b: int = Depends(simple_dependency),
    c: int = Depends(another_dependency),
):
    return a + b + c

@pytest.mark.asyncio
async def test_async_dependency():
    assert 6 == await method("1")
