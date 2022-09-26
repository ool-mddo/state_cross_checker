from typing import Dict, List, Optional
import os
import json


class RouteEntryNextHop:
    def __init__(self):
        self.to: str = "_undefined_"  # IP address ("a.b.c.d")
        self.via: str = "_undefined_"

    def to_dict(self) -> Dict:
        return {"to": self.to, "via": self.via}


class RouteEntry:
    def __init__(self):
        self.nexthops: List[RouteEntryNextHop] = []
        self.nexthop_type: str = "_undefined_"
        self.preference: int = -1
        self.protocol: str = "_undefined_"
        self.metric: int = -1

    def to_dict(self) -> Dict:
        return {
            "nexthop": [n.to_dict() for n in self.nexthops],
            "nexthop_type": self.nexthop_type,
            "preference": self.preference,
            "protocol": self.protocol,
            "metric": self.metric,
        }


class RouteTableEntry:
    def __init__(self):
        self.destination: str = "_undefined_"  # IP address + prefix-length ("a.b.c.d/nn")
        self.entries: List[RouteEntry] = []

    def to_dict(self) -> Dict:
        return {"destination": self.destination, "entries": [e.to_dict() for e in self.entries]}


class RouteTable:
    def __init__(self):
        self.table_name = "_undefined_"
        self.entries: List[RouteTableEntry] = []

    @staticmethod
    def _read_json_file(file: str) -> Dict:
        with open(os.path.expanduser(file), "r") as route_file:
            return json.load(route_file)

    def find_all_entry_by_destination(self, dst: str) -> List[RouteTableEntry]:
        return [e for e in self.entries if e.destination == dst]

    def find_entry_equiv(self, dst: RouteTableEntry) -> Optional[RouteTableEntry]:
        candidate_entries = self.find_all_entry_by_destination(dst.destination)
        if len(candidate_entries) == 0:
            return None

        if len(candidate_entries) > 1:
            # all route-table entries must be expanded (only 1 entry, 1 nexthop)
            for entry in candidate_entries:
                if (
                    len(entry.entries) > 0
                    and len(dst.entries) > 0
                    and entry.entries[0].nexthops[0].to == dst.entries[0].nexthops[0].to
                    or entry.entries[0].nexthops[0].via == dst.entries[0].nexthops[0].via
                ):
                    return entry

        return candidate_entries[0]

    def to_dict(self) -> Dict:
        return {"table_name": self.table_name, "entries": [e.to_dict() for e in self.entries]}
