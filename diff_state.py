# NOTICE: export PYTHONPATH="./src"
from src.base_ospfneigh_table import OspfNeighborTable
from src.base_route_table import RouteTable
from src.batfish_ospfneigh_table import BatfishOspfNeighborTable
from src.batfish_route_table import BatfishRouteTable
from src.cisco_ospfneigh_table import CiscoOspfNeighborTable
from src.cisco_route_table import CiscoRouteTable
from src.juniper_ospfneigh_table import JuniperOspfNeighborTable
from src.juniper_route_table import JuniperRouteTable
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


def read_config(config_file: str, target_nw: str, target_ss: str) -> Dict:
    # load config (config template)
    env = Environment(loader=FileSystemLoader("./", encoding="UTF-8"))
    template = env.get_template(config_file)
    template_param = {"network_name": target_nw, "snapshot_name": target_ss}

    # render & parse config
    config_string = template.render(template_param)
    return yaml.safe_load(config_string)


def choose_config(config_file: str, target_env: str, target_nw: str, target_ss: str) -> Dict:
    config_data = read_config(config_file, target_nw, target_ss)
    return config_data[target_env]


def join_as_path(*path) -> str:
    return os.path.expanduser(os.path.join(*path))


def route_table(config: Dict, node_param: Dict) -> RouteTable:
    node_name = node_param['name'] if config["type"] == "original" else node_param['name'].lower()
    file_name = f"{node_name}{config['routes_file']}"
    file_path = join_as_path(config["state_dir"], config["routes_dir"], file_name)
    if config["type"] == "batfish":
        return BatfishRouteTable(file_path)
    if config["type"] == "emulated" or config["type"] == "original" and node_param["type"] == "juniper":
        rt = JuniperRouteTable(file_path)
        rt.expand_rt_entry()
        return rt
    # config type = original and not juniper node
    return CiscoRouteTable(file_path)


def ospf_neighbor_table(config: Dict, node_param: Dict) -> OspfNeighborTable:
    node_name = node_param['name'] if config["type"] == "original" else node_param['name'].lower()
    file_name = f"{node_name}{config['ospf_neighbors_file']}"
    file_path = join_as_path(config["state_dir"], config["ospf_neighbors_dir"], file_name)
    if config["type"] == "batfish":
        return BatfishOspfNeighborTable(file_path)
    if config["type"] == "emulated" or config["type"] == "original" and node_param["type"] == "juniper":
        return JuniperOspfNeighborTable(file_path)
    # config type = original and not juniper node
    return CiscoOspfNeighborTable(file_path)


def check_state_table_for_node(target_table: str, node_param: Dict) -> Dict:
    if target_table == "route":
        src_rt = route_table(src_config, node_param)
        dst_rt = route_table(dst_config, node_param)
        if args.debug:
            return {"node_param": node_param, "src": src_rt.to_dict(), "dst": dst_rt.to_dict()}
        else:
            return {"node_param": node_param, "result": cross_check(src_rt, dst_rt)}
    elif target_table == "ospf_neighbor":
        # ignore non-ospf-speaker
        if node_param["ospf"] is False:
            return {"node_param": node_param, "result": {}, "note": "ignored (non-ospf-speaker)"}

        src_ospf_neigh = ospf_neighbor_table(src_config, node_param)
        dst_ospf_neigh = ospf_neighbor_table(dst_config, node_param)
        if args.debug:
            return {"node_param": node_param, "src": src_ospf_neigh.to_dict(), "dst": dst_ospf_neigh.to_dict()}
        else:
            return {"node_param": node_param, "result": cross_check(src_ospf_neigh, dst_ospf_neigh)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross check routing table")
    parser.add_argument("--config", "-c", type=str, help="Config file")
    parser.add_argument(
        "--table", "-t", required=True, choices=["route", "ospf_neighbor"], help="Choice target state table"
    )
    parser.add_argument("--debug", action="store_true", help="raw data to debug")
    # target
    parser.add_argument("--network", "-n", required=True, type=str, help="Target network")
    parser.add_argument("--node", "-d", type=str, help="Target node (device)")
    # target snapshot (source)
    parser.add_argument(
        "--src-env", "-se", required=True, choices=["batfish", "original", "emulated"], help="Choose source env"
    )
    parser.add_argument("--src-snapshot", "-ss", required=True, type=str, help="Source snapshot name")
    # target snapshot (destination)
    parser.add_argument(
        "--dst-env", "-de", required=True, choices=["batfish", "original", "emulated"], help="Choose destination env"
    )
    parser.add_argument("--dst-snapshot", "-ds", required=True, type=str, help="Destination snapshot name")
    parser.add_argument("--output", "-o", choices=["json", "yaml"], default="yaml", help="Output format")

    args = parser.parse_args()

    if not os.path.exists(os.path.expanduser(args.config)):
        util.error("config file not found")

    config_data = read_config(args.config, args.network, args.src_snapshot)
    original_node_params = config_data["original_node_params"]
    src_config = choose_config(args.config, args.src_env, args.network, args.src_snapshot)
    dst_config = choose_config(args.config, args.dst_env, args.network, args.dst_snapshot)

    if args.debug:
        print("# DEBUG: src_config: ", src_config, file=sys.stderr)
        print("# DEBUG: dst_config: ", dst_config, file=sys.stderr)
        print("# DEBUG: original_node_params: ", original_node_params, file=sys.stderr)

    result_data = []
    if args.node:
        # for a node
        # find a node param by name (ignore case)
        node_param = next(filter(lambda n: n["name"].lower() == args.node.lower(), original_node_params), None)
        if args.debug:
            print("# DEBUG: node_param: ", node_param, file=sys.stderr)
        if node_param is not None:
            result_data.append(check_state_table_for_node(args.table, node_param))
        else:
            print(f"Error: node {args.node} is not found in config", file=sys.stderr)
            sys.exit(1)
    else:
        # for all nodes
        for node_param in original_node_params:
            if args.debug:
                print("# DEBUG: node_param: ", node_param, file=sys.stderr)
            result_data.append(check_state_table_for_node(args.table, node_param))

    # output
    output_data = {"src_env": args.src_env, "dst_env": args.dst_env, "all_results": result_data}
    if args.output == "json":
        print(json.dumps(output_data))
    else:
        print(yaml.dump(output_data))  # default
