from dataclasses import dataclass
from .state import ConnectionState

@dataclass
class PartialFlock:
    id: int
    
    def attach_state(self, state: ConnectionState):
        self._connection_state = state
        return self