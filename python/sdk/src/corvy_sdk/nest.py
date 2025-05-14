

from dataclasses import dataclass
from .flock import PartialFlock
from .state import ConnectionState

@dataclass
class PartialNest:
    id: int
    flock: PartialFlock # needed to fetch info
    
    def attach_state(self, state: ConnectionState):
        self._connection_state = state
        return self