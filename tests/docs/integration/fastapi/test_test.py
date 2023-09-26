from docs.docs_src.integrations.fastapi.test_kafka import test_router as test_k
from docs.docs_src.integrations.fastapi.test_rabbit import test_router as test_r
from docs.docs_src.integrations.fastapi.test_nats import test_router as test_n


__all__ = (
    "test_k",
    "test_r",
    "test_n",
)
