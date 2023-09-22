from datetime import datetime

import pytest
from freezegun import freeze_time

from faststream._compat import model_to_jsonable
from faststream.kafka import TestKafkaBroker

from .app import CourseUpdates, broker, on_course_update


@broker.subscriber("notify_updates")
async def on_notify_update(msg: CourseUpdates):
    pass


# Feeze time so the datetime always uses the same time
@freeze_time("2023-01-01")
@pytest.mark.asyncio
async def test_app_without_new_content():
    async with TestKafkaBroker(broker):
        timestamp = datetime.now()
        await broker.publish(
            CourseUpdates(course_name="Biology", timestamp=timestamp), "course_updates"
        )

        course_json = model_to_jsonable(
            CourseUpdates(course_name="Biology", timestamp=timestamp)
        )
        on_course_update.mock.assert_called_with(course_json)
        on_notify_update.mock.assert_called_with(course_json)


# Feeze time so the datetime always uses the same time
@freeze_time("2023-01-01")
@pytest.mark.asyncio
async def test_app_with_new_content():
    async with TestKafkaBroker(broker):
        timestamp = datetime.now()
        await broker.publish(
            CourseUpdates(
                course_name="Biology",
                new_content="We have additional classes...",
                timestamp=timestamp,
            ),
            "course_updates",
        )
        course_json = model_to_jsonable(
            CourseUpdates(
                course_name="Biology",
                new_content="We have additional classes...",
                timestamp=timestamp,
            )
        )
        on_course_update.mock.assert_called_with(course_json)

        on_update_json = model_to_jsonable(
            CourseUpdates(
                course_name="Updated: Biology",
                new_content="We have additional classes...",
                timestamp=timestamp,
            )
        )
        on_notify_update.mock.assert_called_with(on_update_json)
