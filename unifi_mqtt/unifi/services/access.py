import json

from .base import UnifiService


class UnifiAccessService(UnifiService):
    name = "access"

    def websocket_url(self):
        return (
            f"wss://{self.controller.host}/proxy/access/ulp-go/api/v2/ws/notification"
        )

    async def on_message(self, msg):
        if not isinstance(msg, dict):
            self.logger.debug("unknown-event: %s", msg)
            return

        if msg["event"] in ("access.logs.add", "access.capture.add"):
            msg["data"] = json.loads(msg["data"])

        await self.emit(msg["event"], msg)
