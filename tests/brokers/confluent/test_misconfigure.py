import pytest

from faststream import AckPolicy
from faststream.confluent import KafkaBroker, TopicPartition
from faststream.exceptions import SetupError


def test_deprecated_options(queue: str) -> None:
    broker = KafkaBroker()

    with pytest.warns(DeprecationWarning):
        broker.subscriber(queue, group_id="test", auto_commit=False)

    with pytest.warns(DeprecationWarning):
        broker.subscriber(queue, auto_commit=True)

    with pytest.warns(DeprecationWarning):
        broker.subscriber(queue, group_id="test", no_ack=False)

    with pytest.warns(DeprecationWarning):
        broker.subscriber(queue, group_id="test", no_ack=True)


def test_deprecated_conflicts_actual(queue: str) -> None:
    broker = KafkaBroker()

    with pytest.raises(SetupError), pytest.warns(DeprecationWarning):
        broker.subscriber(queue, auto_commit=False, ack_policy=AckPolicy.ACK)

    with pytest.raises(SetupError), pytest.warns(DeprecationWarning):
        broker.subscriber(queue, no_ack=False, ack_policy=AckPolicy.ACK)


def test_manual_ack_policy_without_group(queue: str) -> None:
    broker = KafkaBroker()

    broker.subscriber(queue, group_id="test", ack_policy=AckPolicy.DO_NOTHING)

    with pytest.raises(SetupError):
        broker.subscriber(queue, ack_policy=AckPolicy.DO_NOTHING)


def test_manual_commit_without_group(queue: str) -> None:
    broker = KafkaBroker()

    with pytest.warns(DeprecationWarning):
        broker.subscriber(queue, group_id="test", auto_commit=False)

    with pytest.raises(SetupError), pytest.warns(DeprecationWarning):
        broker.subscriber(queue, auto_commit=False)


def test_wrong_destination(queue: str) -> None:
    broker = KafkaBroker()

    with pytest.raises(SetupError):
        broker.subscriber()

    with pytest.raises(SetupError):
        broker.subscriber(queue, partitions=[TopicPartition(queue, 1)])
