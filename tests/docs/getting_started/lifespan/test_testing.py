from docs.docs_src.getting_started.lifespan.kafka.testing import (
    test_lifespan as test_lifespan_k,
)
from docs.docs_src.getting_started.lifespan.nats.testing import (
    test_lifespan as test_lifespan_n,
)
from docs.docs_src.getting_started.lifespan.rabbit.testing import (
    test_lifespan as test_lifespan_r,
)
from docs.docs_src.getting_started.lifespan.redis.testing import (
    test_lifespan as test_lifespan_red,
)

__all__ = (
    "test_lifespan_k",
    "test_lifespan_r",
    "test_lifespan_n",
    "test_lifespan_red",
)
