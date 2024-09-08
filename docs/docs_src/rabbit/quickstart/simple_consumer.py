import asyncio
from faststream import FastStream
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
        max_consumers=10, # Will take no more than 10 messages in advance (aka prefetch count)
    )
    app = FastStream(broker)

    @broker.subscriber("test-queue", retry=True)
    async def handle(msg):
        print(msg)

    await app.run()

if __name__ == "__main__":
    asyncio.run(main())