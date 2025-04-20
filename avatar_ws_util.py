import asyncio
import json
import logging
from typing import Optional
from aiohttp import ClientSession, WSMsgType, WSMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AvatarWsUtil:
    def __init__(self, request_url: str):
        self.request_url = request_url
        self.websocket = None
        self.is_connected = False
        self.connect_event = asyncio.Event()
        self.countdown_latch = None

    async def connect(self):
        """
        建立websocket 连接
        """
        async with ClientSession() as session:
            self.websocket = await session.ws_connect(self.request_url)
            self.is_connected = True
            self.connect_event.set()
            logger.info("WebSocket connected")

            async for msg in self.websocket:
                await self._handle_message(msg)

    async def _handle_message(self, msg: WSMessage):
        if msg.type == WSMsgType.TEXT:
            logger.info(f"Received message: {msg.data}")
            try:
                data = json.loads(msg.data)
                header = data.get("header", {})
                code = header.get("code", -1)

                if code != 0:
                    await self._handle_error(
                        code, header.get("message", "Unknown error"), "server closed"
                    )
                    return

                payload = data.get("payload", {})
                if payload:
                    avatar = payload.get("avatar", {})
                    if avatar and avatar.get("stream_url"):
                        if self.countdown_latch:
                            self.countdown_latch.set()

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")

        elif msg.type == WSMsgType.ERROR:
            logger.error(f"WebSocket error: {msg.data}")
            self.is_connected = False
            if self.countdown_latch:
                self.countdown_latch.set()

        elif msg.type == WSMsgType.CLOSE:
            logger.info("WebSocket closed")
            self.is_connected = False
            if self.countdown_latch:
                self.countdown_latch.set()

    async def _handle_error(self, code: int, reason: str, event: str):
        logger.error(f"Session {event}. Code: {code}, Reason: {reason}")
        self.is_connected = False
        if self.countdown_latch:
            self.countdown_latch.set()
        if self.websocket:
            await self.websocket.close(code=code, message=reason.encode())

    async def start(
        self, request: dict, countdown_latch: Optional[asyncio.Event] = None
    ):
        self.countdown_latch = countdown_latch
        await self.connect_event.wait()
        await self.send(request)

    async def send(self, request: dict):
        if self.is_connected and self.websocket:
            json_str = json.dumps(request)
            logger.info(f"Sending: {json_str}")
            await self.websocket.send_str(json_str)

    async def close(self):
        if self.websocket:
            await self.websocket.close(code=1000, message=b"Normal closure")
            self.is_connected = False
