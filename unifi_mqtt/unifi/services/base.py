from enum import Enum

import aiohttp
import logging

USER_AGENT = "unifi-mqtt/1.0"


class UnifiService:
    name = None

    def __init__(
        self,
        controller,
    ):
        self.controller = controller

        self.ws = None

        self.is_closed = False
        self.is_reconnecting = False
        self.auto_reconnect_interval = 5

        self.logger = logging.getLogger(f"unifi_mqtt.unifi.{self.name}")

    def websocket_url(self) -> str:
        raise NotImplementedError

    async def on_message(self, msg):
        raise NotImplementedError

    async def on_binary_message(self, msg):
        raise NotImplementedError

    async def connect(self, reconnect=False):
        self.is_closed = False
        self.is_reconnecting = False
        await self.login(reconnect=reconnect)
        await self.listen()

    async def close(self):
        self.is_closed = True
        self.is_reconnected = False
        if self.ws:
            await self.ws.close()

    async def emit(self, event: str, payload: dict = None):
        return await self.controller.emit(self.name, event, payload)

    async def listen(self):
        try:
            self.ws = await self.controller.session.ws_connect(
                url=self.websocket_url(),
                heartbeat=15,
                verify_ssl=self.controller.verify_ssl,
                compress=False,
            )
        except aiohttp.ClientError as exc:
            await self.emit(self.name, "error", exc)
            return

        await self._on_open()
        while True:
            msg = await self.ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                await self._on_message(msg.json())
            elif msg.type == aiohttp.WSMsgType.BINARY:
                await self._on_binary_message(msg)
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                await self._on_close()
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                await self._on_error(self.ws.exception())
                break

    async def _on_open(self):
        self.is_reconnecting = False
        return await self.controller.on_websocket_open(self)

    async def _on_close(self):
        return await self.controller.on_websocket_close(self)

    async def _on_error(self, exc):
        return await self.controller.on_websocket_error(self, exc)

    async def _on_binary_message(self, msg):
        try:
            await self.on_binary_message(msg)
        except Exception as exc:
            await self._on_error(exc)

    async def _on_message(self, msg):
        try:
            await self.on_message(msg)
        except Exception as exc:
            await self._on_error(exc)
