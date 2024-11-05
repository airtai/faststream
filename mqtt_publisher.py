import asyncio

from aiomqtt import Client


async def main():
    async with Client("185.102.139.35", port=18831, username='mqtt_user_vps', password='MqttPasswordVps') as client:
        await client.publish("test", payload=28.4, retain=True)


asyncio.run(main())

connection bridge1
address 185.102.139.35
notifications true
notification_topic /clientnotification/bridge1_status
remote_username mqtt_user_vps
remote_password MqttPasswordVps

topic # both