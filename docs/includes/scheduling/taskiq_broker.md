=== "Kafka"
    ```python linenums="1"
    from taskiq_faststream import StreamScheduler
    from taskiq.schedule_sources import LabelScheduleSource

    taskiq_broker.task(
        message={"user": "John", "user_id": 1},
        topic="test-subject",
        schedule=[{
            "cron": "* * * * *",
        }],
    )

    scheduler = StreamScheduler(
        broker=taskiq_broker,
        sources=[LabelScheduleSource(taskiq_broker)],
    )
    ```

=== "RabbitMQ"
    ```python linenums="1"
    from taskiq_faststream import StreamScheduler
    from taskiq.schedule_sources import LabelScheduleSource

    taskiq_broker.task(
        message={"user": "John", "user_id": 1},
        queue="test-queue",
        schedule=[{
            "cron": "* * * * *",
        }],
    )

    scheduler = StreamScheduler(
        broker=taskiq_broker,
        sources=[LabelScheduleSource(taskiq_broker)],
    )
    ```

=== "Nats"
    ```python linenums="1"
    from taskiq_faststream import StreamScheduler
    from taskiq.schedule_sources import LabelScheduleSource

    taskiq_broker.task(
        message={"user": "John", "user_id": 1},
        subject="test-subject",
        schedule=[{
            "cron": "* * * * *",
        }],
    )

    scheduler = StreamScheduler(
        broker=taskiq_broker,
        sources=[LabelScheduleSource(taskiq_broker)],
    )
    ```

=== "Redis"
    ```python linenums="1"
    from taskiq_faststream import StreamScheduler
    from taskiq.schedule_sources import LabelScheduleSource

    taskiq_broker.task(
        message={"user": "John", "user_id": 1},
        channel="test-subject",
        schedule=[{
            "cron": "* * * * *",
        }],
    )

    scheduler = StreamScheduler(
        broker=taskiq_broker,
        sources=[LabelScheduleSource(taskiq_broker)],
    )
    ```
