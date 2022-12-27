import os
import re
import sys
from typing import Dict, NoReturn
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
    def __init__(self, file_path: str):
        super().__init__()

        self.table_name = "_cisco_ospf_neighbor_"
        # pylint: disable=duplicate-code
        self._load_table_data(file_path)

    def _load_table_data(self, file_path: str) -> NoReturn:
        # pylint: disable=duplicate-code
        with open(file_path, encoding="UTF-8") as file_io:
            index = 0
            for line in file_io.read().splitlines():
                index += 1
                print(f"# DEBUG-{index}: LINE={line}", file=sys.stderr)

                # pylint: disable=duplicate-code
                for match_info in self._generate_match_info_list():
                    print(
                        f"# DEBUG-{index}: regexp={match_info['regexp']}, type={match_info['type']}", file=sys.stderr
                    )
                    match = re.search(match_info["regexp"], line)
                    if match:
                        self._add_entry_by_type(match, match_info)

    @staticmethod
    def _generate_match_info_list():
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

        print(f"# DEBUG: {neighbor_id}, {priority}, {state}, {addr}, {intf}", file=sys.stderr)

        self.entries.append(CiscoOspfNeighborTableEntry(mdict))


if __name__ == "__main__":
    BASE_DIR = "~/ool-mddo/playground/configs/mddo-ospf/original_asis/status/showospfneigh"
    # file = os.path.join(BASE_DIR, "RegionB-RT1_show_ospf_neigh.txt")
    file = os.path.join(BASE_DIR, "RegionC-RT1_show_ospf_neigh.txt")
    cisco_rt = CiscoOspfNeighborTable(os.path.expanduser(file))
    print(yaml.dump(cisco_rt.to_dict()))
