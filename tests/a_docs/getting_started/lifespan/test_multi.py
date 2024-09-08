import pytest

from faststream import TestApp, context


@pytest.mark.asyncio
async def test_multi_lifespan():
    from docs.docs_src.getting_started.lifespan.multiple import app

    async with TestApp(app):
        assert context.get("field") == 1
