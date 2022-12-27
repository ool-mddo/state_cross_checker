# NOTICE: export PYTHONPATH="./src"
from src.base_ospfneigh_table import OspfNeighborTable
from src.base_route_table import RouteTable
from src.crpd_route_table import CrpdRouteTable
from src.crpd_ospfneigh_table import CrpdOspfNeighborTable
from src.batfish_route_table import BatfishRouteTable
from src.batfish_ospfneigh_table import BatfishOspfNeighborTable
from src.state_table import StateTable
import src.utility as util
import argparse
from jinja2 import Environment, FileSystemLoader
import json
import os
import sys
from typing import Dict
import yaml


def cross_check(src_table: StateTable, dst_table: StateTable) -> Dict:
    result = {"both": [], "only_src": [], "only_dst": []}
    for dst_table_entry in dst_table.entries:
        src_table_entry = src_table.find_entry_equiv(dst_table_entry)
        if src_table_entry:
            result["both"].append({"src_entry": src_table_entry.to_dict(), "dst_entry": dst_table_entry.to_dict()})
        else:
            result["only_dst"].append(dst_table_entry.to_dict())

    for src_table_entry in src_table.entries:
        dst_table_entry = dst_table.find_entry_equiv(src_table_entry)
        if dst_table_entry:
            continue
        result["only_src"].append(src_table_entry.to_dict())

    return result


def choice_config(config_file: str, target_env: str, target_nw: str, target_ss: str, node: str) -> Dict:
    # load config (config template)
    env = Environment(loader=FileSystemLoader("./", encoding="utf8"))
    template = env.get_template(config_file)
    template_param = {"network_name": target_nw, "snapshot_name": target_ss, "node_name": node}

    # render & parse config
    config_string = template.render(template_param)
    config_data = yaml.safe_load(config_string)

    return config_data[target_env]


def concat_as_path(*path) -> str:
    return os.path.expanduser(os.path.join(*path))


def route_table(config: Dict, node_name: str) -> RouteTable:
    file = concat_as_path(config["state_dir"], node_name, config["ospf_routes_file"])
    if config["type"] == "batfish":
        return BatfishRouteTable(file)

    rt = CrpdRouteTable(file)
    rt.expand_rt_entry()
    return rt


def ospf_neighbor_table(config: Dict, node_name: str) -> OspfNeighborTable:
    file = concat_as_path(config["state_dir"], node_name, config["ospf_neighbors_file"])
    if config["type"] == "batfish":
        return BatfishOspfNeighborTable(file)

    return CrpdOspfNeighborTable(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross check routing table")
    parser.add_argument("--config", "-c", type=str, default="config.tmpl.yaml", help="Config file")
    parser.add_argument(
        "--table", "-t", required=True, choices=["route", "ospf_neighbor"], help="Choice target state table"
    )
    parser.add_argument("--debug", action="store_true", help="raw data to debug")
    # target
    parser.add_argument("--network", "-n", required=True, type=str, help="Target network")
    parser.add_argument("--node", "-d", required=True, type=str, help="Target node (device)")
    # target snapshot (source)
    parser.add_argument(
        "--src-env", "-se", required=True, choices=["batfish", "original", "emulated"], help="Choise source env"
    )
    parser.add_argument("--src-snapshot", "-ss", required=True, type=str, help="Source snapshot name")
    # target snapshot (destination)
    parser.add_argument(
        "--dst-env", "-de", required=True, choices=["batfish", "original", "emulated"], help="Choise destination env"
    )
    parser.add_argument("--dst-snapshot", "-ds", required=True, type=str, help="Destination snapshot name")

    args = parser.parse_args()

    if not os.path.exists(os.path.expanduser(args.config)):
        util.error("config file not found")

    with open(os.path.expanduser(args.config), "r") as config_file:
        src_config = choice_config(args.config, args.src_env, args.network, args.src_snapshot, args.node)
        dst_config = choice_config(args.config, args.dst_env, args.network, args.dst_snapshot, args.node)
        node_name = args.node

        if args.debug:
            print("# DEBUG: src_config : ", src_config, file=sys.stderr)
            print("# DEBUG: dst_config : ", dst_config, file=sys.stderr)

        if args.table == "route":
            src_rt = route_table(src_config, node_name)
            dst_rt = route_table(dst_config, node_name)
            if args.debug:
                print(json.dumps([src_rt.to_dict(), dst_rt.to_dict()]), file=sys.stderr)
            else:
                print(json.dumps(cross_check(src_rt, dst_rt)))
            sys.exit(0)

        if args.table == "ospf_neighbor":
            src_ospf_neigh = ospf_neighbor_table(src_config, node_name)
            dst_ospf_neigh = ospf_neighbor_table(dst_config, node_name)
            if args.debug:
                print(json.dumps([src_ospf_neigh.to_dict(), dst_ospf_neigh.to_dict()]), file=sys.stderr)
            else:
                print(json.dumps(cross_check(src_ospf_neigh, dst_ospf_neigh)))
