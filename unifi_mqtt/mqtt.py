from asyncio_mqtt import Client, MqttError

from .constants import MQTT_DEFAULT_PORT, MQTT_DEFAULT_TOPIC, MQTT_DEFAULT_USERNAME, MQTT_DEFAULT_PASSWORD


class Mqtt:
    def __init__(
        self, host: str, port: int = MQTT_DEFAULT_PORT, username: str = MQTT_DEFAULT_USERNAME,
            password: str = MQTT_DEFAULT_PASSWORD, topic: str = MQTT_DEFAULT_TOPIC
    ):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.topic = topic

        self.self = None

        self.client = Client(hostname=self.host, port=self.port, username=self.username, password=self.password)

    async def connect(self):
        await self.client.connect()

    async def close(self):
        await self.client.disconnect()

    async def publish(self, topic, payload):
        await self.client.publish(f"{self.topic}/{topic}", payload)

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
