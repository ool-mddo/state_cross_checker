import copy
import os
from typing import Dict, List, NoReturn
import yaml
import utility as util
from base_route_table import RouteEntryNextHop, RouteEntry, RouteTableEntry, RouteTable


class JuniperRouteEntryNextHop(RouteEntryNextHop):
    def __init__(self, rt_nh: Dict):
        super().__init__()

        if "to" in rt_nh:
            self.to = rt_nh["to"][0]["data"]

        if "via" in rt_nh:
            self.via = rt_nh["via"][0]["data"]
        else:
            self.via = rt_nh["nh-local-interface"][0]["data"]


class JuniperRouteEntry(RouteEntry):
    def __init__(self, rt_entry: Dict):
        super().__init__()

        if "nh" in rt_entry:
            if len(rt_entry["nh"]) > 1:
                util.warn_multiple("nh", rt_entry["nh"])
            self.nexthops: List[JuniperRouteEntryNextHop] = [JuniperRouteEntryNextHop(n) for n in rt_entry["nh"]]
        if "nh-type" in rt_entry:
            self.nexthop_type = rt_entry["nh-type"][0]["data"]
        if "preference" in rt_entry:
            self.preference = int(rt_entry["preference"][0]["data"])
        if "protocol-name" in rt_entry:
            self.protocol = rt_entry["protocol-name"][0]["data"]
        if "metric" in rt_entry:
            self.metric = int(rt_entry["metric"][0]["data"])


class JuniperRouteTableEntry(RouteTableEntry):
    def __init__(self, rt_data: Dict):
        super().__init__()
        # _debug(f"juniper rt_data: {json.dumps(rt_data)}")

        if len(rt_data["rt-destination"]) > 1:
            util.warn_multiple("rt-destination", rt_data["rt-destination"])

        self.destination = rt_data["rt-destination"][0]["data"]

        if len(rt_data["rt-entry"]) > 1:
            util.warn_multiple("rt-entry", rt_data["rt-entry"])

        self.entries: List[JuniperRouteEntry] = [JuniperRouteEntry(r) for r in rt_data["rt-entry"]]

    def expand_nh(self) -> NoReturn:
        """Expand a entry that have multiple next-hops to multiple entries that have a next-hop"""
        expanded_entries: List[JuniperRouteEntry] = []
        for entry in self.entries:
            if len(entry.nexthops) <= 1:
                expanded_entries.append(entry)  # nothing to do
                continue

            for nexthop in entry.nexthops:
                copy_entry = copy.deepcopy(entry)
                copy_entry.nexthops = [nexthop]
                expanded_entries.append(copy_entry)

        # !!OVERWRITE!!
        self.entries = expanded_entries


class JuniperRouteTable(RouteTable):
    def __init__(self, file_path: str, debug=False):
        super().__init__(debug)
        self.data = self._read_json_file(file_path)

        # contains ipv4/v6 routing table as default
        route_tables = self.data["route-information"][0]["route-table"]
        # find inet.0 table
        self.table_name = "inet.0"
        self.inet0 = next(
            (t for t in route_tables if "table-name" in t and t["table-name"][0]["data"] == self.table_name), None
        )
        if self.inet0 is None:
            util.error_exit(f"inet.0 is not found in {file_path}")

        # route table entries
        self.entries = [JuniperRouteTableEntry(e) for e in self.inet0["rt"]]

    def expand_rt_entry(self) -> NoReturn:
        """Expand a table-entry that have multiple route-entries to multiple table-entries that have a route-entry"""
        expanded_entries: List[JuniperRouteTableEntry] = []
        for entry in self.entries:
            entry.expand_nh()
            if len(entry.entries) <= 1:
                expanded_entries.append(entry)
                continue

            for nexthop in entry.entries:
                copy_entry = copy.deepcopy(entry)
                copy_entry.entries = [nexthop]
                expanded_entries.append(copy_entry)

        # !!OVERWRITE!!
        self.entries = expanded_entries


if __name__ == "__main__":
    BASE_DIR = "~/ool-mddo/playground/configs/mddo-ospf/emulated_asis/status/showroute"
    file = os.path.join(BASE_DIR, "RegionA-RT1_show_route.txt")
    juniper_rt = JuniperRouteTable(os.path.expanduser(file))
    juniper_rt.expand_rt_entry()
    print(yaml.dump(juniper_rt.to_dict()))
