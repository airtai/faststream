import pytest

from faststream.kafka import KafkaBroker


def test_wrong_subscriber() -> None:
    broker = KafkaBroker()

    with pytest.raises(ValueError):  # noqa: PT011
        broker.subscriber("test", auto_commit=False)(lambda: None)
