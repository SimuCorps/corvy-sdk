# flock.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from .state import ConnectionState

if TYPE_CHECKING:
    from .nest import Nest

@dataclass
class PartialFlock:
    id: int

    def attach_state(self, state: ConnectionState) -> PartialFlock:
        self._connection_state = state
        return self

    async def fetch(self) -> Flock:
        """
        Fetch a complete Flock from a PartialFlock.
        """
        url = f"{self._connection_state.api_path}/flocks/{self.id}"
        async with self._connection_state.client_session.get(url) as resp:
            data = await resp.json()
            if not data.get("success", False):
                raise ValueError(data.get("error", data))

        f = data["flock"]

        flock = Flock(
            f["id"], f["name"], f.get("icon"), f["members_count"], f["nests_count"],
            datetime.strptime(f["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc),
        )

        flock.attach_state(self._connection_state)
        return flock

    async def get_nests(self) -> list["Nest"]:
        """Get all nests in this flock."""
        url = f"{self._connection_state.api_path}/flocks/{self.id}/nests"
        async with self._connection_state.client_session.get(url) as resp:
            data = await resp.json()
            if not data.get("success", False):
                raise ValueError(data.get("error", data))

        from .nest import Nest

        nests: list[Nest] = []
        for n in data["nests"]:
            nest = Nest(n["id"], self, n["name"], n["position"], datetime.strptime(n["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc))
            if hasattr(self, "_connection_state"):
                nest.attach_state(self._connection_state)
            nests.append(nest)

        nests.sort(key=lambda x: x.id)
        return nests

@dataclass
class Flock(PartialFlock):
    name: str
    icon: str | None
    member_count: int
    nest_count: int
    created_at: datetime | None

    @staticmethod
    async def _get_all(state: ConnectionState) -> list[Flock]:
        url = f"{state.api_path}/flocks"
        async with state.client_session.get(url) as resp:
            data = await resp.json()
            if not data.get("success", False):
                raise ValueError(data.get("error", data))

        flocks: list[Flock] = []
        for f in data["flocks"]:
            print(f)
            flock = Flock(
                f["id"],
                f["name"],
                f.get("icon"),
                f["members_count"],
                f["nests_count"],
                datetime.strptime(f["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc),
            )
            flock.attach_state(state)
            flocks.append(flock)

        # sort by id ascending
        flocks.sort(key=lambda x: x.id)
        return flocks
