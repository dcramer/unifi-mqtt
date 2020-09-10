import logging
import asyncio
import os

import click

from unifi_mqtt.constants import (
    UNIFI_DEFAULT_HOST,
    UNIFI_DEFAULT_PASSWORD,
    UNIFI_DEFAULT_PORT,
    UNIFI_DEFAULT_USERNAME,
    UNIFI_DEFAULT_SITE,
    DEFAULT_TOPIC,
)

logging.basicConfig(level=logging.INFO)

from .unifi.controller import UnifiController


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
@click.option("--topic", default=DEFAULT_TOPIC)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["error", "warning", "info", "debug"]),
)
def main(host, port, username, password, site, secure, topic, service, log_level):
    os.environ["PYTHONUNBUFFERED"] = "true"

    configure_logging(log_level)

    unifi = UnifiController(
        host=host,
        port=port,
        username=username,
        password=password,
        site=site,
        verify_ssl=secure,
        services=service,
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(unifi.connect())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting Down!")
        loop.close()


if __name__ == "__main__":
    main()
