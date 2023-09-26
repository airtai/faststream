import pytest

from docs.docs_src.getting_started.subscription.real_testing_kafka import (
    test_handle as test_handle_k,
)
from docs.docs_src.getting_started.subscription.real_testing_kafka import (
    test_validation_error as test_validation_error_k,
)
from docs.docs_src.getting_started.subscription.real_testing_rabbit import (
    test_handle as test_handle_r,
)
from docs.docs_src.getting_started.subscription.real_testing_rabbit import (
    test_validation_error as test_validation_error_r,
)
from docs.docs_src.getting_started.subscription.real_testing_nats import (
    test_handle as test_handle_n,
)
from docs.docs_src.getting_started.subscription.real_testing_nats import (
    test_validation_error as test_validation_error_n,
)


pytest.mark.kafka(test_handle_k)
pytest.mark.kafka(test_validation_error_k)

pytest.mark.rabbit(test_handle_r)
pytest.mark.rabbit(test_validation_error_r)

pytest.mark.nats(test_handle_n)
pytest.mark.nats(test_validation_error_n)
