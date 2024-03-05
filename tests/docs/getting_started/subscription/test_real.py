import pytest

from docs.docs_src.getting_started.subscription.confluent.real_testing import (
    test_handle as test_handle_confluent,
)
from docs.docs_src.getting_started.subscription.confluent.real_testing import (
    test_validation_error as test_validation_error_confluent,
)
from docs.docs_src.getting_started.subscription.kafka.real_testing import (
    test_handle as test_handle_k,
)
from docs.docs_src.getting_started.subscription.kafka.real_testing import (
    test_validation_error as test_validation_error_k,
)
from docs.docs_src.getting_started.subscription.nats.real_testing import (
    test_handle as test_handle_n,
)
from docs.docs_src.getting_started.subscription.nats.real_testing import (
    test_validation_error as test_validation_error_n,
)
from docs.docs_src.getting_started.subscription.rabbit.real_testing import (
    test_handle as test_handle_r,
)
from docs.docs_src.getting_started.subscription.rabbit.real_testing import (
    test_validation_error as test_validation_error_r,
)
from docs.docs_src.getting_started.subscription.redis.real_testing import (
    test_handle as test_handle_red,
)
from docs.docs_src.getting_started.subscription.redis.real_testing import (
    test_validation_error as test_validation_error_red,
)

pytest.mark.kafka(test_handle_k)
pytest.mark.kafka(test_validation_error_k)

pytest.mark.kafka(test_handle_confluent)
pytest.mark.kafka(test_validation_error_confluent)

pytest.mark.rabbit(test_handle_r)
pytest.mark.rabbit(test_validation_error_r)

pytest.mark.nats(test_handle_n)
pytest.mark.nats(test_validation_error_n)

pytest.mark.redis(test_handle_red)
pytest.mark.redis(test_validation_error_red)
