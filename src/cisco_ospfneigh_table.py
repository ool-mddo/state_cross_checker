import os
import re
from typing import Dict, List, NoReturn
import yaml
from base_ospfneigh_table import OspfNeighborTable, OspfNeighborTableEntry
from parseable import Parseable
import utility as util


class CiscoOspfNeighborTableEntry(OspfNeighborTableEntry):
    def __init__(self, neighbor_data: Dict):
        super().__init__()

        self.address = neighbor_data["addr"]
        self.interface = neighbor_data["intf"]
        self.state = neighbor_data["state"]
        self.id = neighbor_data["id"]
        self.priority = int(neighbor_data["priority"])


class CiscoOspfNeighborTable(OspfNeighborTable, Parseable):
    def __init__(self, file_path: str, debug=False):
        super().__init__(debug)

        self.table_name = "_cisco_ospf_neighbor_"
        self._load_table_data(file_path)

    # pylint: disable=duplicate-code
    def _load_table_data(self, file_path: str) -> NoReturn:
        with open(file_path, encoding="UTF-8") as file_io:
            index = 0
            for line in file_io.read().splitlines():
                index += 1
                util.debug(f"{index}: LINE={line}", self.debug)

                self._match_line(index, line, self.debug)

    @staticmethod
    def _generate_match_info_list() -> List[Dict]:
        id_re = r"(?P<id>(?:\d+\.){3}\d+)"  # x.x.x.x
        vrf_re = "default"  # only search GRT, not captured
        state_re = r"(?P<state>\w+)\/B?DR"  # state like: "FULL/DR", DR or BDR is ignored
        time_re = r"\d\d:\d\d:\d\d"  # dead time (not captured)
        addr_re = r"(?P<addr>(?:\d+\.){3}\d+)"  # x.x.x.x
        intf_re = r"(?P<intf>[\w\d\/:_]+)"  # NOTICE: almost string...
        instance_re = r"\d+"  # integer (not captured)
        priority_re = r"(?P<priority>\d+)"  # integer

        return [
            {
                "regexp": r"\s+".join([id_re, instance_re, vrf_re, priority_re, state_re, time_re, addr_re, intf_re]),
                "type": "cisco",
            },
            {
                "regexp": r"\s+".join([id_re, priority_re, state_re, time_re, addr_re, intf_re]),
                "type": "arista",
            },
        ]

    def _add_entry_by_type(self, match: re.Match, _match_info: Dict) -> NoReturn:
        mdict = match.groupdict()

        neighbor_id = mdict["id"]
        priority = mdict["priority"]
        state = mdict["state"]
        addr = mdict["addr"]
        intf = mdict["intf"]

        util.debug(f"{neighbor_id}, {priority}, {state}, {addr}, {intf}", self.debug)

        self.entries.append(CiscoOspfNeighborTableEntry(mdict))


if __name__ == "__main__":
    BASE_DIR = "~/ool-mddo/playground/configs/mddo-ospf/original_asis/status/showospfneigh"
    # file = os.path.join(BASE_DIR, "RegionB-RT1_show_ospf_neigh.txt")
    file = os.path.join(BASE_DIR, "RegionC-RT1_show_ospf_neigh.txt")
    cisco_rt = CiscoOspfNeighborTable(os.path.expanduser(file), debug=True)
    print(yaml.dump(cisco_rt.to_dict()))
