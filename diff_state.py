# NOTICE: export PYTHONPATH="./src"
import argparse
import json
import yaml
from src.state_checker import StateChecker
import src.utility as util

if __name__ == "__main__":
    table_choices = ["route", "ospf_neighbor"]
    env_choices = ["batfish", "original", "emulated"]
    output_choices = ["json", "yaml"]

    parser = argparse.ArgumentParser(description="Cross check routing table")
    parser.add_argument("--config", "-c", type=str, help="Config file")
    parser.add_argument("--table", "-t", required=True, choices=table_choices, help="Choice target state table")
    parser.add_argument("--debug", action="store_true", help="raw data to debug")
    parser.add_argument("--output", "-o", choices=output_choices, default="yaml", help="Output format")
    # target
    parser.add_argument("--network", "-n", required=True, type=str, help="Target network")
    parser.add_argument("--node", "-d", type=str, help="Target node (device)")
    # target snapshot (source)
    parser.add_argument("--src-env", "-se", required=True, choices=env_choices, help="Choose source env")
    parser.add_argument("--src-snapshot", "-ss", required=True, type=str, help="Source snapshot name")
    # target snapshot (destination)
    parser.add_argument("--dst-env", "-de", required=True, choices=env_choices, help="Choose destination env")
    parser.add_argument("--dst-snapshot", "-ds", required=True, type=str, help="Destination snapshot name")

    args = parser.parse_args()
    state_checker = StateChecker(
        args.config, args.src_env, args.dst_env, args.network, args.src_snapshot, args.dst_snapshot, args.debug
    )

    result_data = []
    if args.node:
        # for a node
        node_param = state_checker.find_node_param_by_name(args.node)
        util.debug(f"node_param: {node_param}", args.debug)
        if node_param is not None:
            result_data.append(state_checker.check_state_table_for_node(args.table, node_param))
        else:
            util.error_exit(f"Error: node {args.node} is not found in config")
    else:
        # for all nodes
        for node_param in state_checker.config.original_node_params:
            util.debug(f"node_param: {node_param}", args.debug)
            result_data.append(state_checker.check_state_table_for_node(args.table, node_param))

    # output
    output_data = {"src_env": args.src_env, "dst_env": args.dst_env, "all_results": result_data}
    if args.output == "json":
        print(json.dumps(output_data))
    else:
        print(yaml.dump(output_data))  # default
