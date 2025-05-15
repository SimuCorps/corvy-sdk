

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import TYPE_CHECKING
from .flock import PartialFlock
from .state import ConnectionState

if TYPE_CHECKING:
    from .messages import Message

@dataclass
class PartialNest:
    id: int
    flock: PartialFlock # needed to fetch info
    
    def attach_state(self, state: ConnectionState):
        self._connection_state = state
        return self
    
    async def fetch(self) -> "Nest":
        async with self._connection_state.client_session.get(f"{self._connection_state.api_path}/flocks/{self.flock.id}/nests/{self.id}") as response:
            data = await response.json()
            if err := data.get("error", False):
                raise ValueError(err)
            nest = Nest(data["nest"]["id"], self.flock, data["nest"]["name"], data["nest"]["position"], datetime.strptime(data["nest"]["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc))
            if hasattr(self, "_connection_state"):
                nest.attach_state(self._connection_state)
            return nest
    
    async def get_messages(self, limit: int = 50, before_id: int | None = None) -> list["Message"]:
        params: dict[str, int] = {"limit": min(limit, 50)}
        if before_id is not None:
            params["before_id"] = before_id

        url = f"{self._connection_state.api_path}/flocks/{self.flock.id}/nests/{self.id}/messages"

        async with self._connection_state.client_session.get(url, params=params) as resp:
            data = await resp.json()
            if not data.get("success", False):
                raise ValueError(data.get("error", data))

        from .messages import Message, MessageUser

        results: list[Message] = []
        for item in data["messages"]:
            u = item["user"]
            user = MessageUser(u["id"], u["username"], u.get("photo_url"), u["is_bot"])
            msg = Message(
                item["id"], item["content"], self.flock, self,
                datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc),
                user
            )
            if hasattr(self, "_connection_state"):
                msg.attach_state(self._connection_state)
            results.append(msg)
        results.sort(key=lambda m: m.id)

        return results
    
    async def send(self, content: str):
        await self._connection_state.websocket.send(json.dumps(
            {
                "topic": self._connection_state.bot_channel,
                "event": "send_message",
                "payload": {
                    "flock_id": self.flock.id,
                    "nest_id": self.id,
                    "content": content
                },
                "ref": "_py_msg"
            }
        )) 
        
    
    
@dataclass
class Nest(PartialNest):
    name: str
    position: int
    created_at: datetime | None