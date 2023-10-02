from docs.docs_src.index.test_kafka import test_correct as test_k_correct
from docs.docs_src.index.test_kafka import test_invalid as test_k_invalid
from docs.docs_src.index.test_nats import test_correct as test_n_correct
from docs.docs_src.index.test_nats import test_invalid as test_n_invalid
from docs.docs_src.index.test_rabbit import test_correct as test_r_correct
from docs.docs_src.index.test_rabbit import test_invalid as test_r_invalid

__all__ = (
    "test_k_correct",
    "test_k_invalid",
    "test_r_correct",
    "test_r_invalid",
    "test_n_correct",
    "test_n_invalid",
)
