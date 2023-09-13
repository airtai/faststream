import pytest

from faststream.kafka import TestKafkaBroker

from .app import Student, broker, on_application, to_class


@pytest.mark.asyncio
async def test_app():
    async with TestKafkaBroker(broker):
        await broker.publish(
            Student(name="Student Studentis", age=12), "student_application"
        )
        on_application.mock.assert_called_with(
            dict(Student(name="Student Studentis", age=12))
        )
        to_class.mock.assert_called_with(
            dict(Student(name="Student Studentis", age=12))
        )
