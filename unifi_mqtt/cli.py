import logging
import asyncio
import os

import click
import netaddr

from .mqtt import Mqtt
from .unifi.controller import UnifiController
from .translator import Translator
from .constants import (
    UNIFI_DEFAULT_HOST,
    UNIFI_DEFAULT_PASSWORD,
    UNIFI_DEFAULT_PORT,
    UNIFI_DEFAULT_USERNAME,
    UNIFI_DEFAULT_SITE,
    MQTT_DEFAULT_HOST,
    MQTT_DEFAULT_PORT,
    MQTT_DEFAULT_NAME,
    MQTT_DEFAULT_USERNAME,
    MQTT_DEFAULT_PASSWORD,
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
@click.option("--unifi-host", default=UNIFI_DEFAULT_HOST)
@click.option("--unifi-port", default=UNIFI_DEFAULT_PORT, type=int)
@click.option("--unifi-username", default=UNIFI_DEFAULT_USERNAME)
@click.option("--unifi-password", default=UNIFI_DEFAULT_PASSWORD)
@click.option("--unifi-site", default=UNIFI_DEFAULT_SITE)
@click.option("--unifi-service", multiple=True, default=["network"])
@click.option("--secure/--insecure", default=True)
@click.option("--mqtt-host", default=MQTT_DEFAULT_HOST)
@click.option("--mqtt-port", default=MQTT_DEFAULT_PORT, type=int)
@click.option("--mqtt-name", default=MQTT_DEFAULT_NAME)
@click.option("--mqtt-username", default=MQTT_DEFAULT_USERNAME)
@click.option("--mqtt-password", default=MQTT_DEFAULT_PASSWORD)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["error", "warning", "info", "debug"]),
)
def main(
    unifi_host,
    unifi_port,
    unifi_username,
    unifi_password,
    unifi_site,
    unifi_service,
    secure,
    log_level,
    mqtt_host,
    mqtt_port,
    mqtt_name,
    mqtt_username,
    mqtt_password,
):
    os.environ["PYTHONUNBUFFERED"] = "true"

    configure_logging(log_level)

    mqtt = Mqtt(
        host=mqtt_host,
        port=mqtt_port,
        name=mqtt_name,
        username=mqtt_username,
        password=mqtt_password,
    )

    # enable unsafe mode for aiohttp's ClientSession CookieJar if unifi_host is IP address instead of FQDN
    try:
        # check if unifi_host is a valid IP address
        netaddr.IPAddress(unifi_host)
        use_unsafe_cookie_jar = True
    except netaddr.AddrFormatError:
        # a netaddr.AddrFormatError exception indicates that unifi_host is not a valid IPv4/IPv6 address
        use_unsafe_cookie_jar = False

    controller = UnifiController(
        host=unifi_host,
        port=unifi_port,
        username=unifi_username,
        password=unifi_password,
        site=unifi_site,
        verify_ssl=secure,
        use_unsafe_cookie_jar=use_unsafe_cookie_jar,
        services=unifi_service,
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
