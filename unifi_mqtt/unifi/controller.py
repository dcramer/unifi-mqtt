import asyncio
import aiohttp
import logging

from typing import List

from ..constants import (
    UNIFI_DEFAULT_HOST,
    UNIFI_DEFAULT_PASSWORD,
    UNIFI_DEFAULT_PORT,
    UNIFI_DEFAULT_USERNAME,
    UNIFI_DEFAULT_SITE,
)
from .services.base import UnifiService
from .services.access import UnifiAccessService
from .services.network import UnifiNetworkService
from .services.protect import UnifiProtectService

logger = logging.getLogger("unifi_mqtt.unifi")


USER_AGENT = "unifi-mqtt/1.0"

SERVICES = {
    "access": UnifiAccessService,
    "network": UnifiNetworkService,
    "protect": UnifiProtectService,
}


class UnifiController:
    def __init__(
        self,
        host: str = UNIFI_DEFAULT_HOST,
        port: int = UNIFI_DEFAULT_PORT,
        username: str = UNIFI_DEFAULT_USERNAME,
        password: str = UNIFI_DEFAULT_PASSWORD,
        site: str = UNIFI_DEFAULT_SITE,
        verify_ssl: bool = True,
        services: List[str] = ["network"],
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.site = site
        self.verify_ssl = verify_ssl

        self.url = f"https://{host}:{port}"

        self.services = tuple(SERVICES[k](self) for k in services)

        self.session = aiohttp.ClientSession(
            raise_for_status=True, headers={"User-Agent": USER_AGENT}
        )

        self.is_closed = False
        self.is_reconnecting = False
        self.auto_reconnect_interval = 5
        self.handlers = []

    async def connect(self, reconnect=False):
        self.is_closed = False
        self.is_reconnecting = False
        await self.login(reconnect=reconnect)
        await self.listen()

    async def close(self):
        self.is_closed = True
        self.ws.close()

    async def login(self, reconnect=False):
        # clear cookies otherwise unifi throws a 404 on next login
        self.session.cookie_jar.clear()
        await self.emit("controller", "login")
        try:
            await self.session.post(
                f"{self.url}/api/auth/login",
                data={
                    "username": self.username,
                    "password": self.password,
                },
                headers={
                    "Referer": f"{self.url}/login",
                },
                verify_ssl=self.verify_ssl,
            )
            logger.info("auth.success")
        except aiohttp.ClientError as exc:
            logger.info("auth.failed")
            if reconnect:
                await self._reconnect()
        except Exception as exc:
            logger.exception(str(exc))

    def add_handler(self, callback):
        self.handlers.append(callback)

    def remove_handler(self, callback):
        self.handlers.remove(callback)

    async def emit(self, name: str, event: str, payload: dict = None):
        logger.debug(f"controller.emit {name}.{event}")
        for handler in self.handlers:
            await handler(name, event, payload)

    async def listen(self):
        for service in self.services:
            await service.close()

        listeners = []
        for service in self.services:
            listeners.append(service.listen())

        results = await asyncio.gather(*listeners, return_exceptions=True)
        for result in results:
            if isinstance(result, BaseException):
                await self.on_service_error(result)

    async def on_websocket_open(self, service: UnifiService):
        self.is_reconnecting = False
        await self.emit(service.name, "connect")

    async def on_websocket_close(self, service: UnifiService):
        await self.emit(service.name, "close")
        await self._reconnect()

    async def on_websocket_error(self, service: UnifiService, exc: BaseException):
        logger.exception(str(exc))
        await self.emit(service.name, "error", exc)
        await self._reconnect()

    async def _reconnect(self):
        if self.is_reconnecting or self.is_closed:
            return

        self.is_reconnecting = True

        await asyncio.sleep(self.auto_reconnect_interval)
        await self.emit("controller", "reconnect")
        await self.connect(True)

    async def _ensure_logged_in(self):
        try:
            await self.session.get(
                f"{self.url}/api/users/self",
                verify_ssl=self.verify_ssl,
            )
        except Exception as exc:
            await self.login()

    def _url(self, path: str) -> str:
        if path.startswith("/"):
            return f"{self.url}{path}"
        return f"{self.url}/api/s/{self.site}/{path}"

    async def get(self, path):
        await self._ensure_logged_in()
        return await self.session.get(
            self._url(path),
            verify_ssl=self.verify_ssl,
        )

    async def delete(self, path):
        await self._ensure_logged_in()
        return await self.session.delete(self._url(path))

    async def post(self, path, data):
        await self._ensure_logged_in()
        return await self.session.post(
            self._url(path),
            data=data,
            verify_ssl=self.verify_ssl,
        )

    async def put(self, path, data):
        await self._ensure_logged_in()
        return await self.session.put(
            self._url(path),
            data=data,
            verify_ssl=self.verify_ssl,
        )
