import logging
import json
from dataclasses import dataclass, field
from time import time
from typing import List, Optional, Union

from .mqtt import Mqtt
from .unifi.controller import UnifiController


logger = logging.getLogger("unifi_mqtt.translator")


@dataclass
class Event:
    topic: str
    data: dict = field(default_factory=dict)


# def format_topic(name, event):
#     return "{}/{}".format(name, event.replace(".", "/"))


def serialize_network(event, payload):
    if event == "EVT_WU_Disconnected":
        return Event(
            f"wifi/{payload['ssid']}/client/{payload['hostname']}",
            {
                "connected": False,
                "mac": payload["user"],
                "ts": payload["time"],
            },
        )
    if event == "EVT_WU_Connected":
        return Event(
            f"wifi/{payload['ssid']}/client/{payload['hostname']}",
            {
                "connected": True,
                "mac": payload["user"],
                "ts": payload["time"],
            },
        )
    if event == "EVT_LU_Connected":
        return Event(
            f"lan/{payload['network']}/client/{payload['hostname']}",
            {
                "connected": True,
                "mac": payload["user"],
                "ts": payload["time"],
            },
        )
    if event == "EVT_LU_Disconnected":
        return Event(
            f"lan/{payload['network']}/client/{payload['hostname']}",
            {
                "connected": False,
                "mac": payload["user"],
                "ts": payload["time"],
            },
        )
    return None, {}


def serialize_access(event, payload):
    if event == "access.logs.add":
        source = payload["data"]["_source"]
        if source["event"]["type"] == "access.door.unlock":
            data = {
                "success": source["event"]["result"] == "ACCESS",
                "actor": {
                    "id": source["actor"]["id"],
                    "display_name": source["actor"]["display_name"],
                },
                "ts": source["event"]["published"],
            }
            events = [
                Event(
                    f"device/{payload['device_id']}/unlock",
                    data,
                )
            ]
            for target in source["target"]:
                events.append(
                    Event(
                        f"target/{target['id']}/unlock",
                        {
                            "name": target["display_name"],
                            "type": target["type"],
                            **data,
                        },
                    )
                )
            return events


def serialize(name, event, payload) -> Union[Optional[Event], List[Event]]:
    if event in ("connected", "disconnected"):
        return Event(event)

    if name == "network":
        return serialize_network(event, payload)
    if name == "access":
        return serialize_access(event, payload)
    print(event, payload)


class Translator:
    def __init__(self, mqtt: Mqtt):
        self.mqtt = mqtt

    def connect(self, controller: UnifiController):
        controller.add_handler(self.on_emit)

    def disconnect(self, controller: UnifiController):
        controller.remove_handler(self.on_emit)

    async def on_emit(self, service_name: str, event_name: str, payload: dict):
        try:
            event_or_events = serialize(service_name, event_name, payload)
        except Exception as exc:
            logger.exception("serialize-error")
            return

        if not event_or_events:
            return

        if isinstance(event_or_events, Event):
            events = [event_or_events]
        else:
            events = event_or_events

        for event in events:
            await self.mqtt.publish(
                f"{service_name}/{event.topic}",
                json.dumps(
                    {
                        "raw": payload,
                        "service": service_name,
                        "event": event_name,
                        # set a default timestamp
                        "ts": int(time() * 1000),
                        **event.data,
                    }
                ),
            )
