from .base import UnifiService

IGNORE_EVENTS = frozenset(["sta:sync", "device:sync", "device:update"])


class UnifiNetworkService(UnifiService):
    name = "network"

    def websocket_url(self):
        return f"wss://{self.controller.host}/proxy/network/wss/s/{self.controller.site}/events"

    async def on_message(self, msg):
        meta = msg["meta"]
        for entry in msg["data"]:
            await self.handle_event(meta["message"], entry)

    async def handle_event(self, type: str, data):
        if type in IGNORE_EVENTS:
            return
        if type == "events":
            key = data["key"]

        await self.emit(f"{self.name}.message", type, data)
