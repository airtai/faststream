from docs.docs_src.getting_started.publishing.kafka.direct_testing import (
    test_handle as test_handle_k,
)
from docs.docs_src.getting_started.publishing.nats.direct_testing import (
    test_handle as test_handle_n,
)
from docs.docs_src.getting_started.publishing.rabbit.direct_testing import (
    test_handle as test_handle_r,
)
from docs.docs_src.getting_started.publishing.redis.direct_testing import (
    test_handle as test_handle_red,
)

__all__ = (
    "test_handle_r",
    "test_handle_k",
    "test_handle_n",
    "test_handle_red",
)
