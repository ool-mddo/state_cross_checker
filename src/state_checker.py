import os
from typing import Dict
from base_ospfneigh_table import OspfNeighborTable
from base_route_table import RouteTable
from batfish_ospfneigh_table import BatfishOspfNeighborTable
from batfish_route_table import BatfishRouteTable
from cisco_ospfneigh_table import CiscoOspfNeighborTable
from cisco_route_table import CiscoRouteTable
from config_loader import ConfigLoader
from juniper_ospfneigh_table import JuniperOspfNeighborTable
from juniper_route_table import JuniperRouteTable
from state_table import StateTable


class StateChecker:
    def __init__(
        self, config_file: str, src_env: str, dst_env: str, network: str, src_ss: str, dst_ss: str, debug=False
    ):
        self.config = ConfigLoader(config_file, src_env, dst_env, network, src_ss, dst_ss, debug)

    @staticmethod
    def _cross_check(src_table: StateTable, dst_table: StateTable) -> Dict:
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

    def find_node_param_by_name(self, node_name):
        """find a node param by name (ignore case)"""
        next(filter(lambda n: n["name"].lower() == node_name.lower(), self.config.original_node_params), None)

    @staticmethod
    def _join_as_path(*path) -> str:
        return os.path.expanduser(os.path.join(*path))

    def _route_table(self, config: Dict, node_param: Dict) -> RouteTable:
        node_name = node_param["name"] if config["type"] == "original" else node_param["name"].lower()
        file_name = f"{node_name}{config['routes_file']}"
        file_path = self._join_as_path(config["state_dir"], config["routes_dir"], file_name)
        if config["type"] == "batfish":
            return BatfishRouteTable(file_path)
        if config["type"] == "emulated" or config["type"] == "original" and node_param["type"] == "juniper":
            route_table = JuniperRouteTable(file_path)
            route_table.expand_rt_entry()
            return route_table
        # config type = original and not juniper node
        return CiscoRouteTable(file_path)

    def _ospf_neighbor_table(self, config: Dict, node_param: Dict) -> OspfNeighborTable:
        node_name = node_param["name"] if config["type"] == "original" else node_param["name"].lower()
        file_name = f"{node_name}{config['ospf_neighbors_file']}"
        file_path = self._join_as_path(config["state_dir"], config["ospf_neighbors_dir"], file_name)
        if config["type"] == "batfish":
            return BatfishOspfNeighborTable(file_path)
        if config["type"] == "emulated" or config["type"] == "original" and node_param["type"] == "juniper":
            return JuniperOspfNeighborTable(file_path)
        # config type = original and not juniper node
        return CiscoOspfNeighborTable(file_path)

    def check_state_table_for_node(self, target_table: str, node_param: Dict, debug=False) -> Dict:
        """Exec cross-check for a node in src/dst environments"""
        if target_table == "route":
            src_rt = self._route_table(self.config.src_config, node_param)
            dst_rt = self._route_table(self.config.dst_config, node_param)
            if debug:
                return {"node_param": node_param, "src": src_rt.to_dict(), "dst": dst_rt.to_dict()}
            return {"node_param": node_param, "result": self._cross_check(src_rt, dst_rt)}

        if target_table == "ospf_neighbor":
            # ignore non-ospf-speaker
            if node_param["ospf"] is False:
                return {"node_param": node_param, "result": {}, "note": "ignored (non-ospf-speaker)"}

            src_ospf_neigh = self._ospf_neighbor_table(self.config.src_config, node_param)
            dst_ospf_neigh = self._ospf_neighbor_table(self.config.dst_config, node_param)
            if debug:
                return {"node_param": node_param, "src": src_ospf_neigh.to_dict(), "dst": dst_ospf_neigh.to_dict()}
            return {"node_param": node_param, "result": self._cross_check(src_ospf_neigh, dst_ospf_neigh)}

        return {"type": "error", "message": f"Unknown target table {target_table}"}
