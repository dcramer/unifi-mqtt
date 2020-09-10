import logging

from .mqtt import Mqtt
from .unifi.controller import UnifiController


logger = logging.getLogger("unifi_mqtt.translator")


class Translator:
    def __init__(self, mqtt: Mqtt):
        self.mqtt = mqtt

    def connect(self, controller: UnifiController):
        controller.add_handler(self.on_emit)

    def disconnect(self, controller: UnifiController):
        controller.remove_handler(self.on_emit)

    async def on_emit(self, event: str, *args):
        logger.debug("emit.receive %s", event)
        pass
