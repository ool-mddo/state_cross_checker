import argparse
import json
from pybatfish.client.session import Session
import os
import pandas as pd
import sys
from typing import Dict, List


def bfq_node_list(bf: Session) -> List[str]:
    df = bf.q.nodeProperties(properties="Configuration_Format").answer().frame()
    return df["Node"].values.tolist()


def bfq_routes_df(bf: Session, node: str) -> pd.DataFrame:
    return bf.q.routes(nodes=node).answer().frame()


def bfq_ospf_session_df(bf: Session, node: str) -> pd.DataFrame:
    return bf.q.ospfSessionCompatibility(nodes=node).answer().frame()


def save_df_as_json(df: pd.DataFrame, dir: str, file: str) -> None:
    file_path = os.path.expanduser(os.path.join(dir, file))
    with open(file_path, "w", encoding="UTF-8") as csv_file:
        csv_file.write(df.to_json(orient="records"))


def exec_queries(sim_env_config: Dict) -> None:
    bf = Session(sim_env_config["bf_host"])
    bf.set_network(sim_env_config["bf_nw_name"])
    bf.init_snapshot(
        os.path.expanduser(sim_env_config["bf_nw_dir"]), name=sim_env_config["bf_ss_name"], overwrite=True
    )
    bf.set_snapshot(sim_env_config["bf_ss_name"])
    for node in bfq_node_list(bf):
        print(f"* Node: {node}")
        routes_df = bfq_routes_df(bf, node)
        save_df_as_json(routes_df, sim_env_config["ospf_routes_dir"], node + "_route.json")
        neighbors_df = bfq_ospf_session_df(bf, node)
        save_df_as_json(neighbors_df, sim_env_config["ospf_routes_dir"], node + "_ospfneigh.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross check routing table")
    parser.add_argument("--config", "-c", type=str, default="config.json", help="config file")
    args = parser.parse_args()

    if not args.config:
        print("ERROR: config file not found", file=sys.stderr)
        sys.exit(1)

    with open(os.path.expanduser(args.config), "r") as config_file:
        config_data = json.load(config_file)
        exec_queries(config_data["sim_env"])
