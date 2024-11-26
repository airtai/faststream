import pytest

from faststream.exceptions import SetupError
from faststream.kafka import KafkaBroker


def test_max_workers_with_manual(queue: str) -> None:
    broker = KafkaBroker()

    with pytest.raises(SetupError):
        broker.subscriber(queue, max_workers=3, auto_commit=False)
