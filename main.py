# NOTICE: export PYTHONPATH="./src"
from src.crpd_route_table import CrpdRouteTable
from src.crpd_ospfneigh_table import CrpdOspfNeighborTable
from src.batfish_route_table import BatfishRouteTable
from src.batfish_ospfneigh_table import BatfishOspfNeighborTable
from src.state_table import StateTable
import src.utility as util
import argparse
import json
import os
import sys
from typing import Dict


def cross_check(crpd_table: StateTable, bf_table: StateTable) -> Dict:
    result = {"both": [], "only_crpd": [], "only_bf": []}
    for bf_table_entry in bf_table.entries:
        crpd_table_entry = crpd_table.find_entry_equiv(bf_table_entry)
        if crpd_table_entry:
            result["both"].append({"crpd_entry": crpd_table_entry.to_dict(), "bf_entry": bf_table_entry.to_dict()})
        else:
            result["only_bf"].append(bf_table_entry.to_dict())

    for crpd_table_entry in crpd_table.entries:
        bf_table_entry = bf_table.find_entry_equiv(crpd_table_entry)
        if bf_table_entry:
            continue
        result["only_crpd"].append(crpd_table_entry.to_dict())

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross check routing table")
    parser.add_argument("--config", "-c", type=str, default="config.json", help="config file")
    parser.add_argument("--table", "-t", required=True, choices=["route", "ospfneigh"], help="select target state table")
    parser.add_argument("--debug", action='store_true', help="raw data to debug")
    args = parser.parse_args()

    if not os.path.exists(os.path.expanduser(args.config)):
        util.error("config file not found")

    with open(os.path.expanduser(args.config), "r") as config_file:
        config_data = json.load(config_file)

        if args.table == "route":
            crpd_rt = CrpdRouteTable(config_data["dev_env"]["ospf_routes_file"])
            bf_rt = BatfishRouteTable(config_data["sim_env"]["ospf_routes_file"])
            if args.debug:
                print(json.dumps([crpd_rt.to_dict(), bf_rt.to_dict()]))
            else:
                crpd_rt.expand_rt_entry()
                print(json.dumps(cross_check(crpd_rt, bf_rt)))
            sys.exit(0)

        if args.table == "ospfneigh":
            crpd_ospfneigh = CrpdOspfNeighborTable(config_data["dev_env"]["ospf_neighbors_file"])
            bf_ospfneigh = BatfishOspfNeighborTable(config_data["sim_env"]["ospf_neighbors_file"])
            if args.debug:
                print(json.dumps([crpd_ospfneigh.to_dict(), bf_ospfneigh.to_dict()]))
            else:
                print(json.dumps(cross_check(crpd_ospfneigh, bf_ospfneigh)))
