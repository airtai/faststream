from docs.docs_src.getting_started.publishing.confluent.object_testing import (
    test_handle as test_handle_confluent,
)
from docs.docs_src.getting_started.publishing.kafka.object_testing import (
    test_handle as test_handle_k,
)
from docs.docs_src.getting_started.publishing.nats.object_testing import (
    test_handle as test_handle_n,
)
from docs.docs_src.getting_started.publishing.rabbit.object_testing import (
    test_handle as test_handle_r,
)
from docs.docs_src.getting_started.publishing.redis.object_testing import (
    test_handle as test_handle_red,
)

__all__ = (
    "test_handle_k",
    "test_handle_r",
    "test_handle_n",
    "test_handle_red",
    "test_handle_confluent",
)
