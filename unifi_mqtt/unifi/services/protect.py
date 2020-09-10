from .base import UnifiService


class UnifiProtectService(UnifiService):
    name = "protect"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.last_update_id = "51b1b10b-6d9f-4817-ab2c-811db24f6bf0"

    def websocket_url(self):
        if self.last_update_id:
            return f"wss://{self.controller.host}/proxy/protect/ws/updates?lastUpdateId={self.last_update_id}"
        return f"wss://{self.controller.host}/proxy/protect/ws/updates"

    async def on_binary_message(self, msg):
        # TODO: need to identify format
        print(self.name, msg.data)
