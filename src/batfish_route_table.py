from typing import Dict, List
from base_route_table import RouteEntryNextHop, RouteEntry, RouteTableEntry, RouteTable


class BatfishRouteEntryNextHop(RouteEntryNextHop):
    def __init__(self, rt_data: Dict):
        super().__init__()
        self.to = rt_data["Next_Hop_IP"]
        self.via = rt_data["Next_Hop_Interface"]


class BatfishRouteEntry(RouteEntry):
    def __init__(self, rt_data: Dict):
        super().__init__()
        self.nexthops = [BatfishRouteEntryNextHop(rt_data)]
        if "type" in rt_data["Next_Hop"]:
            self.nexthop_type = rt_data["Next_Hop"]["type"]
        self.preference = rt_data["Admin_Distance"]
        self.protocol = rt_data["Protocol"]
        self.metric = rt_data["Metric"]


class BatfishRouteTableEntry(RouteTableEntry):
    def __init__(self, rt_data: Dict):
        super().__init__()
        # _debug(f"bf rt_data: {json.dumps(rt_data)}")

        self.destination = rt_data["Network"]
        self.entries: List[BatfishRouteEntry] = [BatfishRouteEntry(rt_data)]


class BatfishRouteTable(RouteTable):
    def __init__(self, file: str):
        super().__init__()
        self.data = self._read_json_file(file)

        # find default entries of default vrf
        self.table_name = "default"
        self.entries: List[BatfishRouteTableEntry] = [
            BatfishRouteTableEntry(e) for e in self.data if e["VRF"] == self.table_name
        ]
