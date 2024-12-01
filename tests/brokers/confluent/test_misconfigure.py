import pytest

from faststream.confluent import KafkaBroker
from faststream.exceptions import SetupError


def test_max_workers_with_manual(queue: str) -> None:
    broker = KafkaBroker()

    with pytest.raises(SetupError):
        broker.subscriber(queue, max_workers=3, auto_commit=False)
