import asyncio
from unifi_mqtt.constants import (
    UNIFI_DEFAULT_HOST,
    UNIFI_DEFAULT_PASSWORD,
    UNIFI_DEFAULT_PORT,
    UNIFI_DEFAULT_USERNAME,
    UNIFI_DEFAULT_SITE,
)
import click
import os

import logging

logging.basicConfig(level=logging.INFO)

from .unifi import UnifiApi


@click.command()
@click.option("--host", default=UNIFI_DEFAULT_HOST)
@click.option("--port", default=UNIFI_DEFAULT_PORT, type=int)
@click.option("--username", default=UNIFI_DEFAULT_USERNAME)
@click.option("--password", default=UNIFI_DEFAULT_PASSWORD)
@click.option("--site", default=UNIFI_DEFAULT_SITE)
@click.option("--secure/--insecure", default=True)
def main(host, port, username, password, site, secure):
    os.environ["PYTHONUNBUFFERED"] = "true"

    unifi = UnifiApi(
        host=host,
        port=port,
        username=username,
        password=password,
        site=site,
        verify_ssl=secure,
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
