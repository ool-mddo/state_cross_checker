import json
import os
from typing import Dict, List, Optional
import utility as util


class OspfNeighborTableEntry:
    def __init__(self):
        self.address: str = "_undefined_"  # IP address
        self.interface: str = "_undefined_"
        self.state: str = "_undefined_"
        self.id: str = "_undefined_"  # IP address (router-id)
        self.priority: int = -1

    def to_dict(self) -> Dict:
        return {
            "address": self.address,
            "interface": self.interface,
            "state": self.state,
            "id": self.id,
            "priority": self.priority,
        }


class OspfNeighborTable:
    def __init__(self):
        self.table_name = "_ospf_neighbor_"
        self.entries: List[OspfNeighborTableEntry] = []

    @staticmethod
    def _read_json_file(file: str) -> Dict:
        with open(os.path.expanduser(file), "r") as route_file:
            return json.load(route_file)

    def find_all_entries_by_address(self, address: str) -> List[OspfNeighborTableEntry]:
        return [e for e in self.entries if e.address == address]

    def find_entry_equiv(self, ospfneigh_entry: OspfNeighborTableEntry) -> Optional[OspfNeighborTableEntry]:
        candidate_entries = self.find_all_entries_by_address(ospfneigh_entry.address)
        if len(candidate_entries) == 0:
            return None
        if len(candidate_entries) > 1:
            # TODO: other attribute matching
            util.warn(f"Found multiple candidate ospf-neighbor-entries: #{json.dumps(candidate_entries)}")

        return candidate_entries[0]

    def to_dict(self) -> Dict:
        return {"table_name": self.table_name, "entries": [e.to_dict() for e in self.entries]}
