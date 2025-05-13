from dataclasses import dataclass
import datetime
from .partials import PartialUser

@dataclass
class MessageUser(PartialUser):
    is_bot: bool
    
@dataclass
class Message:
    id: int
    content: str
    flock_name: str
    flock_id: int
    nest_name: str
    nest_id: int
    created_at: datetime
    user: MessageUser
