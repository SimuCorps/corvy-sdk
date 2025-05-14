from dataclasses import dataclass
import aiohttp

@dataclass
class ConnectionState:
    client_session: aiohttp.ClientSession