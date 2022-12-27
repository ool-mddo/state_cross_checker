from typing import Dict
from base_ospfneigh_table import OspfNeighborTable, OspfNeighborTableEntry
import utility as util


class JuniperOspfNeighborTableEntry(OspfNeighborTableEntry):
    def __init__(self, neighbor_data: Dict):
        super().__init__()
        self.address = neighbor_data["neighbor-address"][0]["data"]
        self.interface = neighbor_data["interface-name"][0]["data"]
        self.state = neighbor_data["ospf-neighbor-state"][0]["data"]
        self.id = neighbor_data["neighbor-id"][0]["data"]
        self.priority = int(neighbor_data["neighbor-priority"][0]["data"])


class JuniperOspfNeighborTable(OspfNeighborTable):
    def __init__(self, file: str):
        super().__init__()
        self.table_name = "_juniper_ospf_neighbor_"
        data = self._read_json_file(file)

        if len(data["ospf-neighbor-information"]) > 1:
            util.warn_multiple("ospf-neighbor-information", data["ospf-neighbor-information"])

        neighbors = data["ospf-neighbor-information"][0]["ospf-neighbor"]
        self.entries = [JuniperOspfNeighborTableEntry(e) for e in neighbors]
