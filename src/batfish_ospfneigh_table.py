from base_ospfneigh_table import OspfNeighborTable, OspfNeighborTableEntry
from typing import Dict


class BatfishOspfNeighborTableEntry(OspfNeighborTableEntry):
    def __init__(self, neighbor_data: Dict):
        super().__init__()
        self.address = neighbor_data["Remote_IP"]
        self.interface = neighbor_data["Remote_Interface"]["hostname"]
        self.state = neighbor_data["Session_Status"]
        # self.id
        # self.priority


class BatfishOspfNeighborTable(OspfNeighborTable):
    def __init__(self, file: str):
        super().__init__()
        self.table_name = "_batfish_ospf_neighbor_"
        data = self._read_json_file(file)

        # find all "default" VRF entries
        neighbors = [d for d in data if d["VRF"] == "default"]
        self.entries = [BatfishOspfNeighborTableEntry(e) for e in neighbors]
