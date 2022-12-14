import os
import re
from typing import Dict, List, NoReturn
import yaml
from base_route_table import RouteEntryNextHop, RouteEntry, RouteTableEntry, RouteTable
from parseable import Parseable
import utility as util


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


class CiscoRouteTable(RouteTable, Parseable):
    LONG_PROTO_TABLE = {"C": "Direct", "L": "Local", "S": "Static", "O": "OSPF", "B": "BGP"}

    def __init__(self, file_path: str, debug=False):
        super().__init__(debug)

        self._load_table_data(file_path)

    # pylint: disable=duplicate-code
    def _load_table_data(self, file_path: str) -> NoReturn:
        with open(file_path, encoding="UTF-8") as file_io:
            index = 0
            for line in file_io.read().splitlines():
                index += 1
                util.debug(f"{index}: LINE={line}", self.debug)

                # there are several differences between cisco/arista show route format
                # - entry lean time
                # - protocol types

                if self._match_line(index, line, self.debug):
                    continue

                # VRF name (routing table name)
                match = re.search(r"VRF: (?P<table_name>.+)", line)
                if match:
                    self.table_name = match.group("table_name")

    @staticmethod
    def _generate_match_info_list() -> List[Dict]:
        proto_re = r"(?P<proto>[CLSOB])"  # connected, local, static, ospf, bgp
        prefix_re = r"(?P<prefix>(?:\d+\.){3}\d+\/\d+)"  # x.x.x.x/xx
        pm_re = r"\[(?P<preference>\d+)\/(?P<metric>\d+)\]"  # preference(admin-distance) and metric
        ip_re = r"(?P<ip>(?:\d+\.){3}\d+)"  # x.x.x.x
        time_re = r"(?:[ywd\d]+)"  # uptime, like "1y2w3d"; not captured
        intf_re = r"(?P<intf>[\w\d\/:_]+)"  # NOTICE: difficult to discriminate between time_re and intf_re

        base_re_list = [
            {"regexp": rf"{proto_re}.+\s+{prefix_re} is directly connected", "type": "direct"},
            {"regexp": rf"{proto_re}.+\s+{prefix_re} {pm_re} via {ip_re}", "type": "entry"},
            {"regexp": rf"^\s*via {ip_re}", "type": "entry_repeat"},
        ]
        # NOTICE: order of suffix check; must both -> time only -> intf only
        # to discriminate ending of the entry is time and/or intf
        suffix_re_list = [rf"{time_re}, {intf_re}", time_re, intf_re]

        # direct product of base_re_list and suffix_re_list
        match_info_list = []
        for base_re in base_re_list:
            for suffix_re in suffix_re_list:
                match_info_list.append(
                    {
                        "regexp": rf"{base_re['regexp']}, {suffix_re}",
                        "type": base_re["type"],
                    }
                )

        return match_info_list

    def _add_entry_by_type(self, match: re.Match, match_info: Dict) -> NoReturn:
        if match_info["type"] == "direct":
            self._add_direct_entry(match.groupdict())
        elif match_info["type"] == "entry":
            self._add_entry(match.groupdict())
        elif match_info["type"] == "entry_repeat":
            self._add_nexthop_to_before_entry(match.groupdict())

    def _add_direct_entry(self, mdict: Dict) -> NoReturn:
        proto = self._long_proto(mdict["proto"])
        prefix = mdict["prefix"]
        intf = mdict["intf"] if "intf" in mdict else None

        util.debug(f"entry (direct) : proto={proto} prefix={prefix}, intf={intf}", self.debug)

        rt_entry = {"protocol": proto, "preference": 0}
        if intf is not None:
            rt_entry["nh"] = [{"via": intf}]

        self.entries.append(CiscoRouteTableEntry({"rt-destination": prefix, "rt-entry": [rt_entry]}))

    def _add_entry(self, mdict: Dict) -> NoReturn:
        proto = self._long_proto(mdict["proto"])
        prefix = mdict["prefix"]
        preference = mdict["preference"]
        metric = mdict["metric"]
        via_ip = mdict["ip"]
        via_intf = mdict["intf"] if "intf" in mdict else None

        util.debug(
            f"entry : proto={proto}, [{preference}/{metric}] prefix={prefix}, ip={via_ip}, intf={via_intf}",
            self.debug,
        )

        rt_entry = {"protocol": proto, "preference": preference, "metric": metric}
        if via_intf is not None:
            rt_entry["nh"] = [{"to": via_ip, "via": via_intf}]
        else:
            rt_entry["nh"] = [{"to": via_ip}]

        self.entries.append(CiscoRouteTableEntry({"rt-destination": prefix, "rt-entry": [rt_entry]}))

    def _add_nexthop_to_before_entry(self, mdict: Dict) -> NoReturn:
        via_ip = mdict["ip"]
        via_intf = mdict["intf"] if "intf" in mdict else None

        util.debug(f"match entry (same dst): ip={via_ip}, intf={via_intf}", self.debug)

        rt_entry: CiscoRouteTableEntry = self.entries[-1]
        if via_intf is not None:
            rt_entry.entries[-1].nexthops.append(CiscoRouteEntryNextHop({"to": via_ip, "via": via_intf}))
        else:
            rt_entry.entries[-1].nexthops.append(CiscoRouteEntryNextHop({"to": via_ip}))

    def _long_proto(self, short):
        if short in self.LONG_PROTO_TABLE:
            return self.LONG_PROTO_TABLE[short]

        util.warn(f"WARNING: unknown protocol: {short}")
        return "_unknown_"


if __name__ == "__main__":
    BASE_DIR = "~/ool-mddo/playground/configs/mddo-ospf/original_asis/status/showroute/"
    file = os.path.join(BASE_DIR, "RegionB-RT1_show_route.txt")
    # file = os.path.join(base_dir, "RegionC-RT1_show_route.txt")
    cisco_rt = CiscoRouteTable(os.path.expanduser(file), debug=True)
    print(yaml.dump(cisco_rt.to_dict()))
