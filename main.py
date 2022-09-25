import argparse
import copy
import json
import os
import sys
from typing import Dict, List, Optional, Type


def _debug(message: str) -> None:
    print(f"DEBUG: {message}", file=sys.stderr)


def _error(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def _warn_multiple(key: str, data: Dict) -> None:
    print(f"WARNING: multiple {key}: {json.dumps(data)}", file=sys.stderr)


class RouteEntryNextHop:
    def __init__(self):
        self.to: str = "_undefined_"  # IP address ("a.b.c.d")
        self.via: str = "_undefined_"

    def to_dict(self) -> Dict:
        return {"to": self.to, "via": self.via}


class RouteEntry:
    def __init__(self):
        self.nexthops: List[Type[RouteEntryNextHop]] = []
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
        self.entries: List[Type[RouteEntry]] = []

    def to_dict(self) -> Dict:
        return {"destination": self.destination, "entries": [e.to_dict() for e in self.entries]}


class RouteTable:
    def __init__(self):
        self.table_name = "_undefined_"
        self.entries: List[Type[RouteTableEntry]] = []

    def find_entry_by_destination(self, dst: str) -> Optional[Type[RouteTableEntry]]:
        return next((e for e in self.entries if e.destination == dst), None)


class BatfishRouteEntryNextHop(RouteEntryNextHop):
    def __init__(self, rt_data: Dict):
        super().__init__()
        self.to = rt_data["Next_Hop_IP"]
        self.via = rt_data["Next_Hop_Interface"]


class BatfishRouteEntry(RouteEntry):
    def __init__(self, rt_data: Dict):
        super().__init__()
        self.nexthops = [BatfishRouteEntryNextHop(rt_data)]
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
        with open(os.path.expanduser(file), "r") as route_file:
            self.data = json.load(route_file)

        # find default entries of default vrf
        self.table_name = "default"
        self.entries: List[BatfishRouteTableEntry] = [
            BatfishRouteTableEntry(e) for e in self.data if e["VRF"] == self.table_name
        ]

    def to_dict(self) -> Dict:
        return {"table_name": self.table_name, "entries": [e.to_dict() for e in self.entries]}


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
            _warn_multiple("rt-destination", rt_data["rt-destination"])

        self.destination = rt_data["rt-destination"][0]["data"]

        if len(rt_data["rt-entry"]) > 1:
            _warn_multiple("rt-entry", rt_data["rt-entry"])

        self.entries: List[CrpdRouteEntry] = [CrpdRouteEntry(r) for r in rt_data["rt-entry"]]

    def expand_nh(self) -> None:
        expanded_entries: List[CrpdRouteEntry] = []
        for entry in self.entries:
            if len(entry.nexthops) <= 1:
                expanded_entries.append(entry)  # nothing to do
                continue

            for i in range(len(entry.nexthops)):
                e = copy.deepcopy(entry)
                e.nexthops = [entry.nexthops[i]]
                expanded_entries.append(e)

        # !!OVERWRITE!!
        self.entries = expanded_entries


class CrpdRouteTable(RouteTable):
    def __init__(self, file: str):
        super().__init__()
        with open(os.path.expanduser(file), "r") as route_file:
            self.data = json.load(route_file)

        # contains ipv4/v6 routing table as default
        route_tables = self.data["route-information"][0]["route-table"]
        # find inet.0 table
        self.table_name = "inet.0"
        self.inet0 = next(
            (t for t in route_tables if "table-name" in t and t["table-name"][0]["data"] == self.table_name), None
        )
        if self.inet0 is None:
            _error(f"inet.0 not found in {file}")
            sys.exit(1)

        # route table entries
        self.entries = [CrpdRouteTableEntry(e) for e in self.inet0["rt"]]

    def to_dict(self) -> Dict:
        return {"table_name": self.table_name, "entries": [e.to_dict() for e in self.entries]}

    def expand_rt_entry(self) -> None:
        expanded_entries: List[CrpdRouteTableEntry] = []
        for entry in self.entries:
            entry.expand_nh()
            if len(entry.entries) <= 1:
                expanded_entries.append(entry)
                continue

            for i in range(len(entry.entries)):
                e = copy.deepcopy(entry)
                e.entries = [entry.entries[i]]
                expanded_entries.append(e)

        # !!OVERWRITE!!
        self.entries = expanded_entries


def cross_check_rt(crpd_rt: CrpdRouteTable, bf_rt: BatfishRouteTable) -> Dict:
    result = {"found": [], "only_crpd_rt": [], "only_bf_rt": []}
    for bf_rt_entry in bf_rt.entries:
        crpd_rt_entry = crpd_rt.find_entry_by_destination(bf_rt_entry.destination)
        if crpd_rt_entry:
            result["found"].append({"crpd_rte": crpd_rt_entry.to_dict(), "bf_rte": bf_rt_entry.to_dict()})
        else:
            result["only_bf_rt"].append(bf_rt_entry.to_dict())

    for crpd_rt_entry in crpd_rt.entries:
        bf_rt_entry = bf_rt.find_entry_by_destination(crpd_rt_entry.destination)
        if bf_rt_entry:
            continue
        result["only_crpd_rt"].append(crpd_rt_entry.to_dict())

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross check routing table")
    parser.add_argument("--config", "-c", type=str, default="config.json", help="config file")
    args = parser.parse_args()

    if not args.config:
        _error("config file not found")

    with open(os.path.expanduser(args.config), "r") as config_file:
        config_data = json.load(config_file)
        crpd_rt = CrpdRouteTable(config_data["dev_env"]["ospf_routes_file"])
        crpd_rt.expand_rt_entry()
        # print(json.dumps(crpd_rt.to_dict()))

        bf_rt = BatfishRouteTable(config_data["sim_env"]["ospf_routes_file"])
        # print(json.dumps(bf_rt.to_dict()))

        # print(json.dumps([crpd_rt.to_dict(), bf_rt.to_dict()]))
        print(json.dumps(cross_check_rt(crpd_rt, bf_rt)))
