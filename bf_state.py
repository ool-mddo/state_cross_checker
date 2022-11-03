import argparse
from jinja2 import Environment, FileSystemLoader
from pybatfish.client.session import Session
import os
import pandas as pd
import re
import sys
from typing import Dict, List
import yaml


def bfq_node_list(bf: Session) -> List[str]:
    df = bf.q.nodeProperties(properties="Configuration_Format").answer().frame()
    return df["Node"].values.tolist()


def bfq_routes_df(bf: Session, node: str) -> pd.DataFrame:
    return bf.q.routes(nodes=node).answer().frame()


def bfq_ospf_session_df(bf: Session, node: str) -> pd.DataFrame:
    return bf.q.ospfSessionCompatibility(nodes=node).answer().frame()


def save_df_as_json(df: pd.DataFrame, directory: str, file: str) -> None:
    directory = os.path.expanduser(directory)
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, file)
    with open(file_path, "w", encoding="UTF-8") as csv_file:
        csv_file.write(df.to_json(orient="records"))


def exec_queries(bf_config: Dict) -> None:
    bf = Session(bf_config["bf_host"])
    bf.set_network(bf_config["bf_nw_name"])
    bf.init_snapshot(os.path.expanduser(bf_config["bf_dir"]), name=bf_config["bf_ss_name"], overwrite=True)
    bf.set_snapshot(bf_config["bf_ss_name"])
    for node in bfq_node_list(bf):
        # ignore segment node (ex: "seg-192.168.0.0-24")
        if re.match(r"seg-(\d+.){3}\d+-\d+", node):
            continue

        print(f"* Node: {node}")
        output_dir = os.path.join(bf_config["state_dir"], node)
        # routing table state
        routes_df = bfq_routes_df(bf, node)
        save_df_as_json(routes_df, output_dir, bf_config["ospf_routes_file"])
        # neighbors table state
        neighbors_df = bfq_ospf_session_df(bf, node)
        save_df_as_json(neighbors_df, output_dir, bf_config["ospf_neighbors_file"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross check routing table")
    parser.add_argument("--config", "-c", type=str, default="config.tmpl.yaml", help="Config file")
    parser.add_argument("--network", "-n", type=str, required=True, help="Target network name")
    parser.add_argument("--snapshot", "-s", type=str, required=True, help="Target snapshot name")
    args = parser.parse_args()

    if not args.config:
        print("ERROR: config file not found", file=sys.stderr)
        sys.exit(1)

    # load config (config template)
    env = Environment(loader=FileSystemLoader("./", encoding="utf8"))
    template = env.get_template(args.config)
    template_param = {"network_name": args.network, "snapshot_name": args.snapshot}
    # render & parse config
    config_string = template.render(template_param)
    config_data = yaml.safe_load(config_string)
    # exec queries
    exec_queries(config_data["batfish"])
