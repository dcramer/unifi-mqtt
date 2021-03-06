import logging
import json
import re
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


mqtt_translation_table = str.maketrans({".": "", " ": "-", "_": "-"})
mqtt_regex_object = re.compile(r"[^a-zA-Z0-9:\-\s]+")


def format_name(name):
    name = name.translate(mqtt_translation_table).lower()
    return mqtt_regex_object.sub("-", name).rstrip("-")


def format_target(target_list):
    targets = {t["type"]: t for t in target_list}
    return "/".join(
        format_name(targets[k]["display_name"])
        for k in ("building", "floor", "door")
        if k in targets
    )


def serialize_network(event, payload):
    # use the device's MAC address instead of its hostname as client_name if a hostname is not available for that client
    if "hostname" in payload:
        client_name = format_name(payload["hostname"])
    else:
        client_name = format_name(payload["user"])

    # use the SSID as the network_name if it's a WLAN event
    if payload["subsystem"] == "wlan" and "ssid" in payload:
        network_name = format_name(payload["ssid"])
    else:
        network_name = format_name(payload["network"])

    if event == "EVT_WU_Disconnected":
        return Event(
            f"wifi/{network_name}/client/{client_name}",
            {
                "connected": False,
                "mac": payload["user"],
                "ts": payload["time"],
            },
        )
    if event == "EVT_WU_Connected":
        return Event(
            f"wifi/{network_name}/client/{client_name}",
            {
                "connected": True,
                "mac": payload["user"],
                "ts": payload["time"],
            },
        )
    if event == "EVT_LU_Connected":
        return Event(
            f"lan/{network_name}/client/{client_name}",
            {
                "connected": True,
                "mac": payload["user"],
                "ts": payload["time"],
            },
        )
    if event == "EVT_LU_Disconnected":
        return Event(
            f"lan/{network_name}/client/{client_name}",
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
            target_path = format_target(source["target"])
            return [
                Event(
                    f"device/{payload['device_id']}/unlock",
                    data,
                ),
                Event(
                    f"target/{target_path}/unlock",
                    data,
                ),
            ]


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
            logger.debug(f"serialize-error/service_name: {service_name}")
            logger.debug(f"serialize-error/event_name: {event_name}")
            logger.debug(f"serialize-error/payload: {payload}")
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
