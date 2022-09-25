import argparse
import json
import os
import sys
from typing import Dict


class RouteTableEntryBase:
    def __init__(self):
        self.destination = None
        self.nexthop_type = None
        self.nexthop_to = None
        self.nexthop_via = None
        self.preference = None
        self.protocol = None
        self.metric = None

    def to_data(self):
        return {
            "destination": self.destination,
            "nexthop": {"type": self.nexthop_type, "to": self.nexthop_to, "via": self.nexthop_via},
            "preference": self.preference,
            "protocol": self.protocol,
            "metric": self.metric,
        }


class BatfishRouteTableEntry(RouteTableEntryBase):
    def __init__(self, rt_data: Dict):
        super().__init__()
        # print(f"# DEBUG: {json.dumps(rt_data)}", file=sys.stderr)

        self.destination = rt_data["Network"]
        self.nexthop_type = rt_data["Next_Hop"]["type"]
        self.nexthop_to = rt_data["Next_Hop_IP"]
        self.nexthop_via = rt_data["Next_Hop_Interface"]
        self.preference = rt_data["Admin_Distance"]
        self.protocol = rt_data["Protocol"]
        self.metric = rt_data["Metric"]


class BatfishRouteTable:
    def __init__(self, file: str):
        with open(os.path.expanduser(file), "r") as route_file:
            self.data = json.load(route_file)

        # find default entries of default vrf
        self.table_name = "default"
        self.entries = [BatfishRouteTableEntry(e) for e in self.data if e["VRF"] == self.table_name]

    def to_data(self) -> Dict:
        return {
            "table_name": self.table_name,
            "entries": [e.to_data() for e in self.entries]
        }


class CrpdRouteTableEntry(RouteTableEntryBase):
    def _warn_multiple(self, key: str, data: Dict) -> None:
        print(f"WARNING: multiple {key}: {json.dumps(data)}", file=sys.stderr)

    def __init__(self, rt_data: Dict):
        super().__init__()
        # print(f"# DEBUG: {json.dumps(rt_data)}", file=sys.stderr)

        if len(rt_data["rt-destination"]) > 1:
            self._warn_multiple("rt-destination", rt_data['rt-destination'])

        self.destination = rt_data["rt-destination"][0]["data"]

        if len(rt_data["rt-entry"]) > 1:
            self._warn_multiple("rt-entry", rt_data['rt-entry'])
        rt_entry = rt_data["rt-entry"][0]

        if "nh" in rt_entry:
            if len(rt_entry["nh"]) > 1:
                self._warn_multiple("nh", rt_entry['nh'])
            nh = rt_entry["nh"][0]

            self.nexthop_to = nh["to"][0]["data"] if "to" in nh else None
            self.nexthop_via = nh["via"][0]["data"] if "via" in nh else nh["nh-local-interface"][0]["data"]
        else:
            self.nexthop_to = None
            self.nexthop_via = None

        self.nexthop_type = rt_entry["nh-type"][0]["data"] if "nh-type" in rt_entry else None
        self.preference = rt_entry["preference"][0]["data"] if "preference" in rt_entry else None
        self.protocol = rt_entry["protocol-name"][0]["data"] if "protocol-name" in rt_entry else None
        self.metric = rt_entry["metric"][0]["data"] if "metric" in rt_entry else None


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
            print(f"ERROR: inet.0 not found in {file}", file=sys.stderr)
            sys.exit(1)

        # route table entries
        self.entries = [CrpdRouteTableEntry(e) for e in self.inet0["rt"]]

    def to_data(self) -> Dict:
        return {"table_name": self.table_name, "entries": [e.to_data() for e in self.entries]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross check routing table")
    parser.add_argument("--config", "-c", type=str, default="config.json", help="config file")
    args = parser.parse_args()

    if not args.config:
        print("ERROR: config file not found", file=sys.stderr)
        sys.exit(1)

    with open(os.path.expanduser(args.config), "r") as config_file:
        config_data = json.load(config_file)
        crpd_rt = CrpdRouteTable(config_data["dev_env"]["ospf_routes_file"])
        print(json.dumps(crpd_rt.to_data()))
        # bf_rt = BatfishRouteTable(config_data["sim_env"]["ospf_routes_file"])
        # print(json.dumps(bf_rt.to_data()))
        # print(json.dumps([crpd_rt.to_data(), bf_rt.to_data()]))
