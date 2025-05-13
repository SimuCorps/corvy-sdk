from dataclasses import dataclass


@dataclass
class PartialUser:
    id: int
    username: str
    