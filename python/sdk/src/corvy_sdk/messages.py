from dataclasses import dataclass
import datetime

from python.sdk.src.corvy_sdk.state import ConnectionState
from .nest import PartialNest
from .flock import PartialFlock
from .user import PartialUser

@dataclass
class MessageUser(PartialUser):
    is_bot: bool
    avatar_url: str | None

@dataclass
class MessageFlock(PartialFlock):
    name: str
    
@dataclass
class MessageNest(PartialNest):
    name: str

@dataclass
class Message:
    id: int
    content: str
    flock: MessageFlock
    nest: MessageNest
    created_at: datetime
    user: MessageUser
    
    
    def attach_state(self, state: ConnectionState):
        self._connection_state = state
        return self
