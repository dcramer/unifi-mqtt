import asyncio
import click
import os

import logging

logging.basicConfig(level=logging.INFO)

from .unifi import UnifiApi


@click.command()
@click.option("--host", default="unifi")
@click.option("--port", default=443, type=int)
@click.option("--username", default="admin")
@click.option("--password", default="ubnt")
@click.option("--site", default="default")
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
