import argparse
import os
import re
import sys
from typing import Dict, List
import yaml
from jinja2 import Environment, FileSystemLoader
from pybatfish.client.session import Session
import pandas as pd


def bfq_node_list(bf_session: Session) -> List[str]:
    """Node list"""
    data_frame = bf_session.q.nodeProperties(properties="Configuration_Format").answer().frame()
    return data_frame["Node"].values.tolist()


def bfq_routes_df(bf_session: Session, node: str) -> pd.DataFrame:
    """Route entries of the node"""
    return bf_session.q.routes(nodes=node).answer().frame()


def bfq_ospf_session_df(bf_session: Session, node: str) -> pd.DataFrame:
    """Ospf neighbors of the node"""
    return bf_session.q.ospfSessionCompatibility(nodes=node).answer().frame()


def save_df_as_json(bf_session: pd.DataFrame, directory: str, file: str) -> None:
    """Save query result (dataframe) to file as the csv file"""
    directory = os.path.expanduser(directory)
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, file)
    with open(file_path, "w", encoding="UTF-8") as csv_file:
        csv_file.write(bf_session.to_json(orient="records"))


def exec_queries(bf_config: Dict) -> None:
    """Query questions to batfish"""
    bf_session = Session(bf_config["bf_host"])
    bf_session.set_network(bf_config["bf_nw_name"])
    bf_session.init_snapshot(os.path.expanduser(bf_config["bf_dir"]), name=bf_config["bf_ss_name"], overwrite=True)
    bf_session.set_snapshot(bf_config["bf_ss_name"])
    for node in bfq_node_list(bf_session):
        # ignore segment node (ex: "seg-192.168.0.0-24")
        if re.match(r"seg-(\d+.){3}\d+-\d+", node):
            continue

        print(f"* Node: {node}")
        output_dir = os.path.join(bf_config["state_dir"], node)
        # routing table state
        routes_df = bfq_routes_df(bf_session, node)
        save_df_as_json(routes_df, output_dir, bf_config["ospf_routes_file"])
        # neighbors table state
        neighbors_df = bfq_ospf_session_df(bf_session, node)
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
