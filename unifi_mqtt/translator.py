import logging
import json
from time import time

from .mqtt import Mqtt
from .unifi.controller import UnifiController


logger = logging.getLogger("unifi_mqtt.translator")


# def format_topic(name, event):
#     return "{}/{}".format(name, event.replace(".", "/"))


def serialize(name, event, payload):
    if event == "connected" or event == "disconnected":
        return event, {}
    if event == "EVT_WU_Disconnected":
        return f"wifi/{payload['ssid']}/client/{payload['hostname']}", {
            "connected": False,
            "mac": payload["user"],
            "ts": payload["time"],
        }
    if event == "EVT_WU_Connected":
        return f"wifi/{payload['ssid']}/client/{payload['hostname']}", {
            "connected": True,
            "mac": payload["user"],
            "ts": payload["time"],
        }
    if event == "EVT_LU_Connected":
        return f"lan/{payload['network']}/client/{payload['hostname']}", {
            "connected": True,
            "mac": payload["user"],
            "ts": payload["time"],
        }
    if event == "EVT_LU_Disconnected":
        return f"lan/{payload['network']}/client/{payload['hostname']}", {
            "connected": False,
            "mac": payload["user"],
            "ts": payload["time"],
        }
    print(event, payload)
    return None, {}


class Translator:
    def __init__(self, mqtt: Mqtt):
        self.mqtt = mqtt

    def connect(self, controller: UnifiController):
        controller.add_handler(self.on_emit)

    def disconnect(self, controller: UnifiController):
        controller.remove_handler(self.on_emit)

    async def on_emit(self, name: str, event: str, payload):
        topic, data = serialize(name, event, payload)
        if not topic:
            return
        await self.mqtt.publish(
            f"{name}/{topic}",
            json.dumps(
                {
                    "raw": payload,
                    "service": name,
                    "event": event,
                    # set a default timestamp
                    "ts": int(time() * 1000),
                    **data,
                }
            ),
        )
