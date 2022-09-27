from typing import Dict, List, Optional
from state_table import StateTableEntry, StateTable


class RouteEntryNextHop:
    def __init__(self):
        # pylint: disable=invalid-name
        self.to: str = "_undefined_"  # IP address ("a.b.c.d")
        self.via: str = "_undefined_"

    def to_dict(self) -> Dict:
        """Convert self to dict"""
        return {"to": self.to, "via": self.via}


class RouteEntry:
    def __init__(self):
        self.nexthops: List[RouteEntryNextHop] = []
        self.nexthop_type: str = "_undefined_"
        self.preference: int = -1
        self.protocol: str = "_undefined_"
        self.metric: int = -1

    def to_dict(self) -> Dict:
        """Convert self to dict"""
        return {
            "nexthop": [n.to_dict() for n in self.nexthops],
            "nexthop_type": self.nexthop_type,
            "preference": self.preference,
            "protocol": self.protocol,
            "metric": self.metric,
        }


class RouteTableEntry(StateTableEntry):
    def __init__(self):
        self.destination: str = "_undefined_"  # IP address + prefix-length ("a.b.c.d/nn")
        self.entries: List[RouteEntry] = []

    def to_dict(self) -> Dict:
        return {"destination": self.destination, "entries": [e.to_dict() for e in self.entries]}


class RouteTable(StateTable):
    def __init__(self):
        super().__init__()
        self.table_name = "_undefined_"
        self.entries: List[RouteTableEntry] = []

    def find_all_entries_by_destination(self, destination: str) -> List[RouteTableEntry]:
        """Find all entries that matches given destination"""
        return [e for e in self.entries if e.destination == destination]

    # pylint: disable=arguments-renamed
    def find_entry_equiv(self, rt_entry: RouteTableEntry) -> Optional[RouteTableEntry]:
        candidate_entries = self.find_all_entries_by_destination(rt_entry.destination)
        if len(candidate_entries) == 0:
            return None

        if len(candidate_entries) > 1:
            # all route-table entries must be expanded (only 1 entry, 1 nexthop)
            for entry in candidate_entries:
                if (
                    len(entry.entries) > 0
                    and len(rt_entry.entries) > 0
                    and entry.entries[0].nexthops[0].to == rt_entry.entries[0].nexthops[0].to
                    or entry.entries[0].nexthops[0].via == rt_entry.entries[0].nexthops[0].via
                ):
                    return entry

        return candidate_entries[0]

    def to_dict(self) -> Dict:
        return {"table_name": self.table_name, "entries": [e.to_dict() for e in self.entries]}
