from typing import Any

import pytest

from faststream import Response
from faststream.confluent.response import KafkaPublishCommand, KafkaResponse
from faststream.response import ensure_response


def test_simple_reponse():
    response = ensure_response(1)
    cmd = KafkaPublishCommand.from_cmd(response.as_publish_command())
    assert cmd.body == 1


def test_base_response_class():
    response = ensure_response(Response(body=1, headers={1: 1}))
    cmd = KafkaPublishCommand.from_cmd(response.as_publish_command())
    assert cmd.body == 1
    assert cmd.headers == {1: 1}


def test_kafka_response_class():
    response = ensure_response(KafkaResponse(body=1, headers={1: 1}, key=b"1"))
    cmd = KafkaPublishCommand.from_cmd(response.as_publish_command())
    assert cmd.body == 1
    assert cmd.headers == {1: 1}
    assert cmd.key == b"1"


@pytest.mark.parametrize(
    ("data", "expected_body"),
    (
        pytest.param(None, (), id="None Response"),
        pytest.param((), (), id="Empty Sequence"),
        pytest.param("123", ("123",), id="String Response"),
        pytest.param("", ("",), id="Empty String Response"),
        pytest.param(b"", (b"",), id="Empty Bytes Response"),
        pytest.param([1, 2, 3], (1, 2, 3), id="Sequence Data"),
        pytest.param([0, 1, 2], (0, 1, 2), id="Sequence Data with False first element"),
    ),
)
def test_batch_response(data: Any, expected_body: Any):
    response = ensure_response(data)
    cmd = KafkaPublishCommand.from_cmd(
        response.as_publish_command(),
        batch=True,
    )
    assert cmd.batch_bodies == expected_body
