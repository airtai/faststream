from docs.docs_src.integrations.fastapi.kafka.test import test_router as test_k
from docs.docs_src.integrations.fastapi.nats.test import test_router as test_n
from docs.docs_src.integrations.fastapi.rabbit.test import test_router as test_r
from docs.docs_src.integrations.fastapi.redis.test import test_router as test_red

__all__ = (
    "test_k",
    "test_r",
    "test_n",
    "test_red",
)
