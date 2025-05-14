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
        pass