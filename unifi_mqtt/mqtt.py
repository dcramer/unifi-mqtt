import logging

from asyncio_mqtt import Client

from .constants import (
    MQTT_DEFAULT_PORT,
    MQTT_DEFAULT_NAME,
    MQTT_DEFAULT_USERNAME,
    MQTT_DEFAULT_PASSWORD,
)


logger = logging.getLogger("unifi_mqtt.mqtt")


class Mqtt:
    def __init__(
        self,
        host: str,
        port: int = MQTT_DEFAULT_PORT,
        username: str = MQTT_DEFAULT_USERNAME,
        password: str = MQTT_DEFAULT_PASSWORD,
        name: str = MQTT_DEFAULT_NAME,
    ):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.name = name

        self.self = None

        self.client = Client(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
        )

    async def connect(self):
        await self.client.connect()

    async def close(self):
        await self.client.disconnect()

    async def publish(self, topic, payload):
        full_topic = f"{self.name}/{topic}"
        logger.debug("mqtt.publish %s", full_topic)

        await self.client.publish(full_topic, payload)

    # # The callback for when the client receives a CONNACK response from the server.
    # def _on_connect(client, userdata, flags, rc):
    #     print("Connected with result code " + str(rc))
    #     pass

    #     # Subscribing in on_connect() means that if we lose the connection and
    #     # reconnect then subscriptions will be renewed.
    #     # client.subscribe("$SYS/#")

    # # The callback for when a PUBLISH message is received from the server.
    # def _on_message(client, userdata, msg):
    #     print(msg.topic + " " + str(msg.payload))
    #     pass
