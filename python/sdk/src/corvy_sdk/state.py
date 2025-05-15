from dataclasses import dataclass
import aiohttp
from websockets.asyncio.client import ClientConnection

@dataclass
class ConnectionState:
    client_session: aiohttp.ClientSession
    websocket: ClientConnection
    bot_channel: str
    api_path: str