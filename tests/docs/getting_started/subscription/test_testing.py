from docs.docs_src.getting_started.subscription.testing_kafka import (
    test_handle as test_handle_k,
)
from docs.docs_src.getting_started.subscription.testing_kafka import (
    test_validation_error as test_validation_error_k,
)
from docs.docs_src.getting_started.subscription.testing_rabbit import (
    test_handle as test_handle_r,
)
from docs.docs_src.getting_started.subscription.testing_rabbit import (
    test_validation_error as test_validation_error_r,
)
from docs.docs_src.getting_started.subscription.testing_nats import (
    test_handle as test_handle_n,
)
from docs.docs_src.getting_started.subscription.testing_nats import (
    test_validation_error as test_validation_error_n,
)


__all__ = (
    "test_handle_r",
    "test_validation_error_r",
    "test_handle_k",
    "test_validation_error_k",
    "test_handle_n",
    "test_validation_error_n",
)
