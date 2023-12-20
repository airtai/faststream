import pytest

from faststream.kafka import KafkaBroker


def test_wrong_subscriber():
    broker = KafkaBroker()

    with pytest.raises(ValueError):
        broker.subscriber("test", auto_commit=False)(lambda: None)
