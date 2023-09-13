import pytest

from faststream.kafka import TestKafkaBroker

from .app import Employee, broker, on_new_employee


@broker.subscriber("notify_accounting")
async def on_notify_accounting(msg: str) -> None:
    pass


@broker.subscriber("notify_all_employees")
async def on_notify_all_employees(msg: str) -> None:
    pass


@pytest.mark.asyncio
async def test_new_employee():
    async with TestKafkaBroker(broker):
        await broker.publish(
            Employee(name="Liam", surname="Neeson", email="linee@mail"), "new_employee"
        )
        on_new_employee.mock.assert_called_once_with(
            dict(Employee(name="Liam", surname="Neeson", email="linee@mail"))
        )

        on_notify_accounting.mock.assert_called_once_with(
            "Please prepare all the paper work for: Liam Neeson"
        )
        on_notify_all_employees.mock.assert_called_once_with(
            "Please welcome our new colleague: Liam Neeson"
        )
