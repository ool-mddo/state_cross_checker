import os
import re
from typing import Dict, List, NoReturn
import yaml
from base_route_table import RouteEntryNextHop, RouteEntry, RouteTableEntry, RouteTable


class CiscoRouteEntryNextHop(RouteEntryNextHop):
    def __init__(self, rt_nh: Dict):
        super().__init__()

        if "to" in rt_nh:
            self.to = rt_nh["to"]
        if "via" in rt_nh:
            self.via = rt_nh["via"]


class CiscoRouteEntry(RouteEntry):
    def __init__(self, rt_entry: Dict):
        super().__init__()

        if "nh" in rt_entry:
            self.nexthops: List[CiscoRouteEntryNextHop] = [CiscoRouteEntryNextHop(n) for n in rt_entry["nh"]]
        if "preference" in rt_entry:
            self.preference = int(rt_entry["preference"])
        if "metric" in rt_entry:
            self.metric = int(rt_entry["metric"])
        if "protocol" in rt_entry:
            self.protocol = rt_entry["protocol"]


class CiscoRouteTableEntry(RouteTableEntry):
    def __init__(self, rt_data: Dict):
        super().__init__()

        self.destination = rt_data["rt-destination"]
        self.entries: List[CiscoRouteEntry] = [CiscoRouteEntry(r) for r in rt_data["rt-entry"]]


class CiscoRouteTable(RouteTable):
    def __init__(self, file: str):
        super().__init__()
        self._load_table_data(file)

    def _load_table_data(self, file: str) -> NoReturn:
        proto_re = r'(?P<proto>[CSOB])'  # connected, static, ospf, bgp
        prefix_re = r'(?P<prefix>(?:\d+\.){3}\d+\/\d+)'  # x.x.x.x/xx
        pm_re = r'\[(?P<preference>\d+)\/(?P<metric>\d+)\]'  # preference(admin-distance) and metric
        ip_re = r'(?P<ip>(?:\d+\.){3}\d+)'  # x.x.x.x
        intf_re = r'(?P<intf>[\w\d\/:_]+)'

        with open(file) as f:
            for line in f.read().splitlines():
                print(line)

                m = re.search(rf"{proto_re}.+\s+{prefix_re} is directly connected, {intf_re}", line)
                if m:
                    self._add_direct_entry(m)
                    continue

                m = re.search(rf"{proto_re}.+\s+{prefix_re} {pm_re} via {ip_re}, {intf_re}", line)
                if m:
                    self._add_entry(m)
                    continue

                m = re.search(rf"VRF: (?P<table_name>.+)", line)
                if m:
                    self.table_name = m.group('table_name')

    def _add_direct_entry(self, match: re.Match) -> NoReturn:
        proto = match.group('proto')
        prefix = match.group('prefix')
        intf = match.group('intf')

        print(f"# DEBUG: match direct connected : proto={proto} prefix={prefix}, intf={intf}")

        rt_entry = {
            "protocol": "Direct",
            "preference": 0,
            "nh": [{"via": intf}]
        }
        self.entries.append(CiscoRouteTableEntry({
            "rt-destination": prefix,
            "rt-entry": [rt_entry]
        }))

    def _add_entry(self, match: re.Match) -> NoReturn:
        proto = self._proto_short_to_long(match.group('proto'))
        prefix = match.group('prefix')
        preference = match.group('preference')
        metric = match.group('metric')
        ip = match.group('ip')
        intf = match.group('intf')
        print(f"# DEBUG: match entry : proto={proto}, [{preference}/{metric}] prefix={prefix}, ip={ip}, intf={intf}")

        rt_entry = {
            "protocol": proto,
            "preference": preference,
            "metric": metric,
            "nh": [{"to": ip, "via": intf}]
        }
        self.entries.append(CiscoRouteTableEntry({
            "rt-destination": prefix,
            "rt-entry": [rt_entry]
        }))

    @staticmethod
    def _proto_short_to_long(short):
        if short == 'C':
            return "Direct"
        if short == 'S':
            return "Static"
        if short == 'O':
            return "OSPF"
        if short == 'B':
            return "BGP"

        print(f"WARNING: unknown protocol: {short}")
        return "_unknown_"


if __name__ == "__main__":
    file = "~/ool-mddo/playground/configs/mddo-ospf/original_asis/status/showroute/RegionB-RT2_show_route.txt"
    cisco_rt = CiscoRouteTable(os.path.expanduser(file))
    print(yaml.dump(cisco_rt.to_dict()))
