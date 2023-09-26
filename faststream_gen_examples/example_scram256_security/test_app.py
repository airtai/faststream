import os
from datetime import date
from unittest import mock

import pytest

from faststream import Context
from faststream._compat import model_to_jsonable
from faststream.kafka import TestKafkaBroker

with mock.patch.dict(
    os.environ,
    {"USERNAME": "username", "PASSWORD": "password"},  # pragma: allowlist secret
):
    from .app import Student, broker, on_application, to_class


@broker.subscriber("class")
async def on_class(
    msg: Student, key: bytes = Context("message.raw_message.key")
) -> None:
    pass


@pytest.mark.asyncio
async def test_app():
    async with TestKafkaBroker(broker):
        birthdate = date(2020, 9, 5)
        await broker.publish(
            Student(name="Student Studentis", birthdate=birthdate),
            "student_application",
        )

        student_json = model_to_jsonable(
            Student(name="Student Studentis", birthdate=birthdate)
        )

        on_application.mock.assert_called_with(student_json)
        to_class.mock.assert_called_with(student_json)
        on_class.mock.assert_called_with(student_json)
