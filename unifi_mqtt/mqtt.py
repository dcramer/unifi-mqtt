import paho.mqtt.client as mqtt


class Mqtt:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.self = None

    async def connect(self):
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self.client.connect(self.host, self.port, 60)

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        self.client.loop_forever()

    async def close(self):
        self.client.disconnect()

    # The callback for when the client receives a CONNACK response from the server.
    def _on_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        pass

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # client.subscribe("$SYS/#")

    # The callback for when a PUBLISH message is received from the server.
    def _on_message(client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        pass
