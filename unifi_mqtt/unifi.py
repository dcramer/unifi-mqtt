import asyncio
import aiohttp
import logging

logger = logging.getLogger("unifi_mqtt.unifi")


USER_AGENT = "unifi-mqtt/1.0"


class UnifiApi:
    def __init__(
        self,
        host: str = "unifi",
        port: int = 443,
        username: str = "admin",
        password: str = "ubnt",
        site: str = "default",
        verify_ssl: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.site = site
        self.verify_ssl = verify_ssl

        self.controller = f"https://{host}:{port}"

        self.session = aiohttp.ClientSession(
            raise_for_status=True, headers={"User-Agent": USER_AGENT}
        )

        self.ws = None

        self.is_closed = False
        self.is_reconnecting = False
        self.auto_reconnect_interval = 5

    async def connect(self, reconnect=False):
        self.is_closed = False
        await self.login(reconnect=reconnect)
        await self.listen()

    async def close(self):
        self.is_closed = True
        self.ws.close()

    async def login(self, reconnect=False):
        try:
            response = await self.session.post(
                f"{self.controller}/api/auth/login",
                data={
                    "username": self.username,
                    "password": self.password,
                },
                headers={
                    "Referer": f"{self.controller}/login",
                },
                verify_ssl=self.verify_ssl,
            )
            logger.info("auth.success")
        except aiohttp.ClientError as exc:
            logger.info("auth.failed")
            self.session.cookie_jar.clear()
            if reconnect:
                await self._reconnect()
        except Exception as exc:
            logger.exception(str(exc))

    async def emit(self, event: str, *args):
        logger.info(event)

    async def listen(self):
        try:
            self.ws = await self.session.ws_connect(
                url=f"wss://{self.host}/proxy/network/wss/s/{self.site}/events",
                heartbeat=15,
                verify_ssl=self.verify_ssl,
                compress=False,
            )
        except aiohttp.ClientError as exc:
            await self.emit("ctrl.error", exc)
            return

        await self._on_open()

        while True:
            msg = await self.ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                await self._on_message(msg)
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                await self._on_close()
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                await self._on_error(self.ws.exception())
                break

    async def _on_open(self):
        self.is_reconnecting = False
        await self.emit("ctrl.connect")

    async def _on_close(self):
        await self.emit("ctrl.close")
        await self._reconnect()

    async def _on_error(self, exc):
        await self.emit("ctrl.error", exc)
        await self._reconnect()

    async def _on_message(self, msg):
        try:
            msg_body = msg.json()
            meta = msg_body["meta"]
            for entry in msg_body["data"]:
                await self._handle_event(meta["message"], entry)
        except Exception as exc:
            await self.emit("ctrl.error", exc)

    async def _reconnect(self):
        if self.is_reconnecting or self.is_closed:
            return

        self.is_reconnecting = True

        await asyncio.sleep(self.auto_reconnect_interval)
        await self.emit("ctrl.reconnect")
        self.is_reconnecting = False
        await self.connect(True)

    async def _handle_event(self, type: str, data):
        await self.emit(f"ctrl.message", type, data)

    async def _ensure_logged_in(self):
        try:
            await self.session.get(
                f"{self.controller}/api/self",
                verify_ssl=self.verify_ssl,
            )
        except Exception as exc:
            await self.login()

    def _url(self, path: str) -> str:
        if path.startswith("/"):
            return f"{self.controller}{path}"
        return f"{self.controller}/api/s/{self.site}/{path}"

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
