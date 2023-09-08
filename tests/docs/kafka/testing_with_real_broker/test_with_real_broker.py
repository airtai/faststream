import pytest

from docs.docs_src.kafka.testing_with_real_broker.test_with_real_broker import (
    test_base_app,
)

pytest.mark.kafka(test_base_app)
