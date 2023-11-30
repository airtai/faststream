from docs.docs_src.index.kafka.test import test_correct as test_k_correct
from docs.docs_src.index.kafka.test import test_invalid as test_k_invalid
from docs.docs_src.index.nats.test import test_correct as test_n_correct
from docs.docs_src.index.nats.test import test_invalid as test_n_invalid
from docs.docs_src.index.rabbit.test import test_correct as test_r_correct
from docs.docs_src.index.rabbit.test import test_invalid as test_r_invalid
from docs.docs_src.index.redis.test import test_correct as test_red_correct
from docs.docs_src.index.redis.test import test_invalid as test_red_invalid

__all__ = (
    "test_k_correct",
    "test_k_invalid",
    "test_r_correct",
    "test_r_invalid",
    "test_n_correct",
    "test_n_invalid",
    "test_red_correct",
    "test_red_invalid",
)
