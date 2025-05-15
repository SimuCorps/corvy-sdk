from dataclasses import dataclass
import datetime

from .state import ConnectionState
from .nest import PartialNest
from .flock import PartialFlock
from .user import PartialUser

@dataclass
class MessageUser(PartialUser):
    is_bot: bool
    avatar_url: str | None

@dataclass
class Message:
    id: int
    content: str
    flock: PartialFlock
    nest: PartialNest
    created_at: datetime
    user: MessageUser
    
    def attach_state(self, state: ConnectionState):
        self._connection_state = state
        return self
