# NOTICE: export PYTHONPATH="./src"

from src.crpd_route_table import CrpdRouteTable
from src.batfish_route_table import BatfishRouteTable
import src.utility as util
import argparse
import json
import os
from typing import Dict


def cross_check_rt(crpd_rt: CrpdRouteTable, bf_rt: BatfishRouteTable) -> Dict:
    result = {"found": [], "only_crpd_rt": [], "only_bf_rt": []}
    for bf_rt_entry in bf_rt.entries:
        crpd_rt_entry = crpd_rt.find_entry_equiv(bf_rt_entry)
        if crpd_rt_entry:
            result["found"].append({"crpd_rte": crpd_rt_entry.to_dict(), "bf_rte": bf_rt_entry.to_dict()})
        else:
            result["only_bf_rt"].append(bf_rt_entry.to_dict())

    for crpd_rt_entry in crpd_rt.entries:
        bf_rt_entry = bf_rt.find_entry_equiv(crpd_rt_entry)
        if bf_rt_entry:
            continue
        result["only_crpd_rt"].append(crpd_rt_entry.to_dict())

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross check routing table")
    parser.add_argument("--config", "-c", type=str, default="config.json", help="config file")
    args = parser.parse_args()

    if not args.config:
        util.error("config file not found")

    with open(os.path.expanduser(args.config), "r") as config_file:
        config_data = json.load(config_file)
        crpd_rt = CrpdRouteTable(config_data["dev_env"]["ospf_routes_file"])
        crpd_rt.expand_rt_entry()
        # print(json.dumps(crpd_rt.to_dict()))

        bf_rt = BatfishRouteTable(config_data["sim_env"]["ospf_routes_file"])
        # print(json.dumps(bf_rt.to_dict()))

        # print(json.dumps([crpd_rt.to_dict(), bf_rt.to_dict()]))
        print(json.dumps(cross_check_rt(crpd_rt, bf_rt)))
