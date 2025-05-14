from .state import ConnectionState
from dataclasses import dataclass
import urllib.parse

@dataclass
class PartialUser:
    id: int | None
    username: str | None
    
    def attach_state(self, state: ConnectionState):
        self._connection_state = state
        return self
    
    async def fetch(self) -> "User":
        async with self._connection_state.client_session.get(f"{self._connection_state.api_path}/users/{self.id}") as response:
            data = await response.json()
            if err := data.get("error", False):
                raise ValueError(err)
            user = User(data["user"]["id"], data["user"]["username"], data["user"]["is_bot"], data["user"]["available_badges"], data["user"].get("photo_url", None), data["user"].get("badge", None))
            if hasattr(self, "_connection_state"):
                user.attach_state(self._connection_state)
            return user
    
    async def fetch_by_username(self) -> "User":
        async with self._connection_state.client_session.get(f"{self._connection_state.api_path}/users/by-username/{urllib.parse.quote_plus(self.username)}") as response:
            data = await response.json()
            if err := data.get("error", False):
                raise ValueError(err)
            user = User(data["user"]["id"], data["user"]["username"], data["user"]["is_bot"], data["user"]["available_badges"], data["user"].get("photo_url", None), data["user"].get("badge", None))
            if hasattr(self, "_connection_state"):
                user.attach_state(self._connection_state)
            return user
    
@dataclass
class User(PartialUser):
    is_bot: bool
    available_badges: list[str]
    avatar_url: str | None
    equipped_badge: str | None