from .state import ConnectionState
from dataclasses import dataclass

@dataclass
class PartialUser:
    id: int
    username: str
    
    def attach_state(self, state: ConnectionState):
        self._connection_state = state
        return self
    
    async def fetch(self) -> "User":
        async with self._connection_state.client_session.get(f"{self._connection_state.api_path}/users/{self.id}") as response:
            data = await response.json()
            return User(data["id"], data["username"], data["is_bot"], data["available_badges"], data.get("photo_url", None), data.get("badge", None))
    
@dataclass
class User(PartialUser):
    is_bot: bool
    available_badges: list[str]
    avatar_url: str | None
    equipped_badge: str | None