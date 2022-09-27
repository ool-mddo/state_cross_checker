from typing import Dict, List, Optional
from state_table import StateTableEntry, StateTable
import utility as util


class OspfNeighborTableEntry(StateTableEntry):
    def __init__(self):
        self.address: str = "_undefined_"  # IP address
        self.interface: str = "_undefined_"
        self.state: str = "_undefined_"
        # pylint: disable=invalid-name
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


class OspfNeighborTable(StateTable):
    def __init__(self):
        super().__init__()
        self.table_name = "_ospf_neighbor_"
        self.entries: List[OspfNeighborTableEntry] = []

    def find_all_entries_by_address(self, address: str) -> List[OspfNeighborTableEntry]:
        """Find all entries that matches given address"""
        return [e for e in self.entries if e.address == address]

    # pylint: disable=arguments-renamed
    def find_entry_equiv(self, ospfneigh_entry: OspfNeighborTableEntry) -> Optional[OspfNeighborTableEntry]:
        candidate_entries = self.find_all_entries_by_address(ospfneigh_entry.address)
        if len(candidate_entries) == 0:
            return None
        if len(candidate_entries) > 1:
            # TODO: other attribute matching
            util.warn(f"Found multiple candidate ospf-neighbor-entries: #{candidate_entries}")

        return candidate_entries[0]

    def to_dict(self) -> Dict:
        return {"table_name": self.table_name, "entries": [e.to_dict() for e in self.entries]}
