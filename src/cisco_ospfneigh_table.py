import os
import re
import sys
from typing import Dict, List, NoReturn
import yaml
from base_ospfneigh_table import OspfNeighborTable, OspfNeighborTableEntry


class CiscoOspfNeighborTableEntry(OspfNeighborTableEntry):
    def __init__(self, neighbor_data: Dict):
        super().__init__()

        self.address = neighbor_data["addr"]
        self.interface = neighbor_data["intf"]
        self.state = neighbor_data["state"]
        self.id = neighbor_data["id"]
        self.priority = int(neighbor_data["priority"])


class CiscoOspfNeighborTable(OspfNeighborTable):
    def __init__(self, file: str):
        super().__init__()
        self.table_name = "_cisco_ospf_neighbor_"
        self._load_table_data(file)

    def _load_table_data(self, file: str) -> NoReturn:
        with open(file) as f:
            index = 0
            for line in f.read().splitlines():
                index += 1
                print(f"# DEBUG-{index}: LINE={line}", file=sys.stderr)

                id_re = r"(?P<id>(?:\d+\.){3}\d+)"  # x.x.x.x
                state_re = r"(?P<state>\w+)\/B?DR"  # state like: "FULL/DR", DR or BDR is ignored
                time_re = r"\d\d:\d\d:\d\d"  # dead time (not captured)
                addr_re = r"(?P<addr>(?:\d+\.){3}\d+)"  # x.x.x.x
                intf_re = r"(?P<intf>[\w\d\/:_]+)"  # NOTICE: almost string...
                instance_re = r"\d+"  # integer (not captured)
                priority_re = r"(?P<priority>\d+)"  # integer

                match_info_list = [
                    {
                        "regexp": rf"{id_re}\s+{instance_re}\s+default\s+{priority_re}\s+{state_re}\s+{time_re}\s+{addr_re}\s+{intf_re}",
                        "type": "cisco",
                    },
                    {
                        "regexp": rf"{id_re}\s+{priority_re}\s+{state_re}\s+{time_re}\s+{addr_re}\s+{intf_re}",
                        "type": "arista",
                    },
                ]
                for match_info in match_info_list:
                    print(f"# DEBUG-{index}: regexp={match_info['regexp']}, type={match_info['type']}", file=sys.stderr)
                    match = re.search(match_info["regexp"], line)
                    if match:
                        self._add_entry_by_type(match, match_info)

    def _add_entry_by_type(self, match: re.Match, _match_info: Dict) -> NoReturn:
        mdict = match.groupdict()

        neighbor_id = mdict["id"]
        priority = mdict["priority"]
        state = mdict["state"]
        addr = mdict["addr"]
        intf = mdict["intf"]

        print(f"# DEBUG: {neighbor_id}, {priority}, {state}, {addr}, {intf}", file=sys.stderr)

        self.entries.append(CiscoOspfNeighborTableEntry(mdict))


if __name__ == "__main__":
    file = "~/ool-mddo/playground/configs/mddo-ospf/original_asis/status/showospfneigh/RegionB-RT1_show_ospf_neigh.txt"
    # file = "~/ool-mddo/playground/configs/mddo-ospf/original_asis/status/showospfneigh/RegionC-RT1_show_ospf_neigh.txt"
    cisco_rt = CiscoOspfNeighborTable(os.path.expanduser(file))
    print(yaml.dump(cisco_rt.to_dict()))
