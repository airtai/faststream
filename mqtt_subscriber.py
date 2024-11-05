import asyncio

from aiomqtt import Client


async def main():
    async with Client("185.102.139.35", port=18831, username='mqtt_user_vps', password='MqttPasswordVps') as client:
        await client.subscribe("/devices/wb-msw-v4_156/controls/Air Quality (VOC)")
        async for message in client.messages:
            print(message)
            print(message.topic)
            print(message.payload)



asyncio.run(main())
