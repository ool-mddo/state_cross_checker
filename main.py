import argparse
import json
import os
import sys
from typing import Dict, List


def _debug(message: str) -> None:
    print(f"DEBUG: {message}", file=sys.stderr)


def _error(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def _warn_multiple(key: str, data: Dict) -> None:
    print(f"WARNING: multiple {key}: {json.dumps(data)}", file=sys.stderr)


class RouteEntryNextHop:
    def __init__(self):
        self.to = None
        self.via = None

    def to_dict(self) -> Dict:
        return {"to": self.to, "via": self.via}


class BatfishRouteEntryNextHop(RouteEntryNextHop):
    def __init__(self, rt_data: Dict):
        super().__init__()
        self.to = rt_data["Next_Hop_IP"]
        self.via = rt_data["Next_Hop_Interface"]


class CrpdRouteEntryNextHop(RouteEntryNextHop):
    def __init__(self, rt_nh: Dict):
        super().__init__()
        self.to = rt_nh["to"][0]["data"] if "to" in rt_nh else None
        self.via = rt_nh["via"][0]["data"] if "via" in rt_nh else rt_nh["nh-local-interface"][0]["data"]


class RouteEntry:
    def __init__(self):
        self.nexthops: List[RouteEntryNextHop] = []
        self.nexthop_type = None
        self.preference = None
        self.protocol = None
        self.metric = None

    def to_dict(self) -> Dict:
        return {
            "nexthop": [n.to_dict() for n in self.nexthops],
            "nexthop_type": self.nexthop_type,
            "preference": self.preference,
            "protocol": self.protocol,
            "metric": self.metric,
        }


class BatfishRouteEntry(RouteEntry):
    def __init__(self, rt_data: Dict):
        super().__init__()
        self.nexthops = [BatfishRouteEntryNextHop(rt_data)]
        self.nexthop_type = rt_data["Next_Hop"]["type"]
        self.preference = rt_data["Admin_Distance"]
        self.protocol = rt_data["Protocol"]
        self.metric = rt_data["Metric"]


class CrpdRouteEntry(RouteEntry):
    def __init__(self, rt_entry: Dict):
        super().__init__()

        if "nh" in rt_entry:
            self.nexthops: List[CrpdRouteEntryNextHop] = [CrpdRouteEntryNextHop(n) for n in rt_entry["nh"]]
        if "nh-type" in rt_entry:
            self.nexthop_type = rt_entry["nh-type"][0]["data"]
        if "preference" in rt_entry:
            self.preference = rt_entry["preference"][0]["data"]
        if "protocol-name" in rt_entry:
            self.protocol = rt_entry["protocol-name"][0]["data"]
        if "metric" in rt_entry:
            self.metric = rt_entry["metric"][0]["data"]


class RouteTableEntry:
    def __init__(self):
        self.destination = None
        self.entries: List[RouteEntry] = []

    def to_dict(self) -> Dict:
        return {"destination": self.destination, "entries": [e.to_dict() for e in self.entries]}


class BatfishRouteTableEntry(RouteTableEntry):
    def __init__(self, rt_data: Dict):
        super().__init__()
        # _debug(f"bf rt_data: {json.dumps(rt_data)}")

        self.destination = rt_data["Network"]
        self.entries: List[BatfishRouteEntry] = [BatfishRouteEntry(rt_data)]


class BatfishRouteTable:
    def __init__(self, file: str):
        with open(os.path.expanduser(file), "r") as route_file:
            self.data = json.load(route_file)

        # find default entries of default vrf
        self.table_name = "default"
        self.entries = [BatfishRouteTableEntry(e) for e in self.data if e["VRF"] == self.table_name]

    def to_dict(self) -> Dict:
        return {"table_name": self.table_name, "entries": [e.to_dict() for e in self.entries]}


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


class CrpdRouteTable:
    def __init__(self, file: str):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross check routing table")
    parser.add_argument("--config", "-c", type=str, default="config.json", help="config file")
    args = parser.parse_args()

    if not args.config:
        _error("config file not found")

    with open(os.path.expanduser(args.config), "r") as config_file:
        config_data = json.load(config_file)
        crpd_rt = CrpdRouteTable(config_data["dev_env"]["ospf_routes_file"])
        # print(json.dumps(crpd_rt.to_dict()))

        bf_rt = BatfishRouteTable(config_data["sim_env"]["ospf_routes_file"])
        # print(json.dumps(bf_rt.to_dict()))

        print(json.dumps([crpd_rt.to_dict(), bf_rt.to_dict()]))
