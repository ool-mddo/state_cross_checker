import copy
import sys
from typing import Dict, List, NoReturn
import utility as util
from base_route_table import RouteEntryNextHop, RouteEntry, RouteTableEntry, RouteTable


class CrpdRouteEntryNextHop(RouteEntryNextHop):
    def __init__(self, rt_nh: Dict):
        super().__init__()
        if "to" in rt_nh:
            self.to = rt_nh["to"][0]["data"]

        if "via" in rt_nh:
            self.via = rt_nh["via"][0]["data"]
        else:
            self.via = rt_nh["nh-local-interface"][0]["data"]


class CrpdRouteEntry(RouteEntry):
    def __init__(self, rt_entry: Dict):
        super().__init__()

        if "nh" in rt_entry:
            if len(rt_entry["nh"]) > 1:
                util.warn_multiple("nh", rt_entry["nh"])
            self.nexthops: List[CrpdRouteEntryNextHop] = [CrpdRouteEntryNextHop(n) for n in rt_entry["nh"]]
        if "nh-type" in rt_entry:
            self.nexthop_type = rt_entry["nh-type"][0]["data"]
        if "preference" in rt_entry:
            self.preference = int(rt_entry["preference"][0]["data"])
        if "protocol-name" in rt_entry:
            self.protocol = rt_entry["protocol-name"][0]["data"]
        if "metric" in rt_entry:
            self.metric = int(rt_entry["metric"][0]["data"])


class CrpdRouteTableEntry(RouteTableEntry):
    def __init__(self, rt_data: Dict):
        super().__init__()
        # _debug(f"crpd rt_data: {json.dumps(rt_data)}")

        if len(rt_data["rt-destination"]) > 1:
            util.warn_multiple("rt-destination", rt_data["rt-destination"])

        self.destination = rt_data["rt-destination"][0]["data"]

        if len(rt_data["rt-entry"]) > 1:
            util.warn_multiple("rt-entry", rt_data["rt-entry"])

        self.entries: List[CrpdRouteEntry] = [CrpdRouteEntry(r) for r in rt_data["rt-entry"]]

    def expand_nh(self) -> NoReturn:
        """Expand a entry that have multiple next-hops to multiple entries that have a next-hop"""
        expanded_entries: List[CrpdRouteEntry] = []
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


class CrpdRouteTable(RouteTable):
    def __init__(self, file: str):
        super().__init__()
        self.data = self._read_json_file(file)

        # contains ipv4/v6 routing table as default
        route_tables = self.data["route-information"][0]["route-table"]
        # find inet.0 table
        self.table_name = "inet.0"
        self.inet0 = next(
            (t for t in route_tables if "table-name" in t and t["table-name"][0]["data"] == self.table_name), None
        )
        if self.inet0 is None:
            util.error(f"inet.0 not found in {file}")
            sys.exit(1)

        # route table entries
        self.entries = [CrpdRouteTableEntry(e) for e in self.inet0["rt"]]

    def expand_rt_entry(self) -> NoReturn:
        """Expand a table-entry that have multiple route-entries to multiple table-entries that have a route-entry"""
        expanded_entries: List[CrpdRouteTableEntry] = []
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
