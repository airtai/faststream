from typing import Any

import pytest
from aiokafka import TopicPartition

from faststream import AckPolicy
from faststream.exceptions import SetupError
from faststream.kafka import KafkaBroker, TopicPartition
from faststream.kafka.subscriber.specified import (
    SpecificationConcurrentBetweenPartitionsSubscriber,
    SpecificationConcurrentDefaultSubscriber,
)


<<<<<<< HEAD
@pytest.mark.parametrize(
    ("args", "kwargs"),
    (
        pytest.param(
            (),
            {},
            id="no destination",
        ),
        pytest.param(
            ("topic",),
            {"partitions": [TopicPartition("topic", 1)]},
            id="topic and partitions",
        ),
        pytest.param(
            ("topic",),
            {"pattern": ".*"},
            id="topic and pattern",
        ),
        pytest.param(
            (),
            {
                "partitions": [TopicPartition("topic", 1)],
                "pattern": ".*",
            },
            id="partitions and pattern",
        ),
    ),
)
def test_wrong_destination(args: list[str], kwargs: dict[str, Any]) -> None:
    with pytest.raises(SetupError):
        KafkaBroker().subscriber(*args, **kwargs)


def test_deprecated_options(queue: str) -> None:
=======
def test_max_workers_with_manual_commit_with_multiple_queues() -> None:
>>>>>>> 60c04eb6d5ecdeef8d958c197adaf2ffef193e2b
    broker = KafkaBroker()

    with pytest.warns(DeprecationWarning):
        broker.subscriber(queue, group_id="test", auto_commit=False)

    with pytest.warns(DeprecationWarning):
        broker.subscriber(queue, auto_commit=True)

    with pytest.warns(DeprecationWarning):
        broker.subscriber(queue, no_ack=False)

    with pytest.warns(DeprecationWarning):
        broker.subscriber(queue, group_id="test", no_ack=True)


def test_deprecated_conflicts_actual(queue: str) -> None:
    broker = KafkaBroker()

    with pytest.raises(SetupError), pytest.warns(DeprecationWarning):
        broker.subscriber(queue, auto_commit=False, ack_policy=AckPolicy.ACK)

    with pytest.raises(SetupError), pytest.warns(DeprecationWarning):
        broker.subscriber(queue, no_ack=False, ack_policy=AckPolicy.ACK)


def test_max_workers_configuration(queue: str) -> None:
    broker = KafkaBroker()

    sub = broker.subscriber(queue, max_workers=3, ack_policy=AckPolicy.ACK_FIRST)
    assert isinstance(sub, SpecificationConcurrentDefaultSubscriber)

    sub = broker.subscriber(queue, max_workers=3, ack_policy=AckPolicy.REJECT_ON_ERROR)
    assert isinstance(sub, SpecificationConcurrentBetweenPartitionsSubscriber)


def test_max_workers_manual_commit_multi_topics_forbidden() -> None:
    with pytest.raises(SetupError):
<<<<<<< HEAD
        KafkaBroker().subscriber(
            "queue1",
            "queue2",
            max_workers=3,
            auto_commit=False,
        )


def test_max_workers_manual_commit_pattern_forbidden() -> None:
    with pytest.raises(SetupError):
        KafkaBroker().subscriber(
            pattern="pattern",
            max_workers=3,
            auto_commit=False,
        )


def test_max_workers_manual_commit_partitions_forbidden() -> None:
    with pytest.raises(SetupError):
        KafkaBroker().subscriber(
=======
        broker.subscriber(["queue1", "queue2"], max_workers=3, auto_commit=False)


def test_max_workers_with_manual_commit_with_pattern() -> None:
    broker = KafkaBroker()

    with pytest.raises(SetupError):
        broker.subscriber(pattern="pattern", max_workers=3, auto_commit=False)


def test_max_workers_with_manual_commit_partitions() -> None:
    broker = KafkaBroker()

    with pytest.raises(SetupError):
        broker.subscriber(
>>>>>>> 60c04eb6d5ecdeef8d958c197adaf2ffef193e2b
            partitions=[TopicPartition(topic="topic", partition=1)],
            max_workers=3,
            auto_commit=False,
        )
