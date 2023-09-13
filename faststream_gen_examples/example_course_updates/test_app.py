import pytest

from faststream.kafka import TestKafkaBroker

from .app import CourseUpdates, broker, on_course_update


@broker.subscriber("notify_updates")
async def on_notify_update(msg: CourseUpdates):
    pass


@pytest.mark.asyncio
async def test_app_without_new_content():
    async with TestKafkaBroker(broker):
        await broker.publish(CourseUpdates(course_name="Biology"), "course_updates")
        on_course_update.mock.assert_called_with(
            dict(CourseUpdates(course_name="Biology"))
        )
        on_notify_update.mock.assert_called_with(
            dict(CourseUpdates(course_name="Biology"))
        )


@pytest.mark.asyncio
async def test_app_with_new_content():
    async with TestKafkaBroker(broker):
        await broker.publish(
            CourseUpdates(
                course_name="Biology", new_content="We have additional classes..."
            ),
            "course_updates",
        )
        on_course_update.mock.assert_called_with(
            dict(
                CourseUpdates(
                    course_name="Biology", new_content="We have additional classes..."
                )
            )
        )
        on_notify_update.mock.assert_called_with(
            dict(
                CourseUpdates(
                    course_name="Updated: Biology",
                    new_content="We have additional classes...",
                )
            )
        )
