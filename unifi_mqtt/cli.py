import logging
import asyncio
import os

import click

from .mqtt import Mqtt
from .unifi.controller import UnifiController
from .translator import Translator
from .constants import (
    UNIFI_DEFAULT_HOST,
    UNIFI_DEFAULT_PASSWORD,
    UNIFI_DEFAULT_PORT,
    UNIFI_DEFAULT_USERNAME,
    UNIFI_DEFAULT_SITE,
    MQTT_DEFAULT_PORT,
    MQTT_DEFAULT_TOPIC,
)

logging.basicConfig(level=logging.INFO)


def configure_logging(log_level):
    logger = logging.getLogger("unifi_mqtt")
    logger.propagate = False
    logger.setLevel(getattr(logging, log_level.upper()))
    while logger.handlers:
        logger.removeHandler(logger.handlers[0])
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s %(message)s"))
    logger.addHandler(handler)


@click.command()
@click.option("--host", default=UNIFI_DEFAULT_HOST)
@click.option("--port", default=UNIFI_DEFAULT_PORT, type=int)
@click.option("--username", default=UNIFI_DEFAULT_USERNAME)
@click.option("--password", default=UNIFI_DEFAULT_PASSWORD)
@click.option("--site", default=UNIFI_DEFAULT_SITE)
@click.option("--secure/--insecure", default=True)
@click.option("--service", multiple=True, default=["network"])
@click.option("--mqtt-host", default="localhost")
@click.option("--mqtt-port", default=MQTT_DEFAULT_PORT, type=int)
@click.option("--topic", default=MQTT_DEFAULT_TOPIC)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["error", "warning", "info", "debug"]),
)
def main(
    host,
    port,
    username,
    password,
    site,
    secure,
    topic,
    service,
    log_level,
    mqtt_host,
    mqtt_port,
):
    os.environ["PYTHONUNBUFFERED"] = "true"

    configure_logging(log_level)

    mqtt = Mqtt(
        host=mqtt_host,
        port=mqtt_port,
    )

    controller = UnifiController(
        host=host,
        port=port,
        username=username,
        password=password,
        site=site,
        verify_ssl=secure,
        services=service,
    )

    translator = Translator(mqtt)
    translator.connect(controller)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(mqtt.connect())
    loop.run_until_complete(controller.connect())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting Down!")
        loop.close()


if __name__ == "__main__":
    main()
