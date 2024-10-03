import asyncio
from faststream.rabbit import RabbitBroker
from faststream.security import SASLPlaintext


async def main():
    broker = RabbitBroker(
        host="localhost",
        port=5672,
        virtualhost="/",
        security=SASLPlaintext(
            username="rabbit",
            password="qwerty123",
        ),
    )
    await broker.connect()
    await broker.publish("Hi!", "test-queue")


if __name__ == "__main__":
    asyncio.run(main())
