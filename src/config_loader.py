import os
from typing import Dict
import yaml
from jinja2 import Environment, FileSystemLoader
import utility as util


class ConfigLoader:
    def __init__(
        self, config_file: str, src_env: str, dst_env: str, network: str, src_ss: str, dst_ss: str, debug=False
    ):
        self.debug = debug
        self.config_file = os.path.expanduser(config_file)
        if not os.path.exists(self.config_file):
            util.error("config file not found")

        config_data = self._read_config(network, src_ss)
        self.original_node_params = config_data["original_node_params"]
        self.src_config = self._choose_config(src_env, network, src_ss)
        self.dst_config = self._choose_config(dst_env, network, dst_ss)

        if self.debug:
            util.debug(f"src_config: {self.src_config}")
            util.debug(f"dst_config: {self.dst_config}")
            util.debug(f"original_node_params: {self.original_node_params}")

    def _read_config(self, target_nw: str, target_ss: str) -> Dict:
        # load config (config template)
        env = Environment(loader=FileSystemLoader("./", encoding="UTF-8"))
        template = env.get_template(self.config_file)
        template_param = {"network_name": target_nw, "snapshot_name": target_ss}

        # render & parse config
        config_string = template.render(template_param)
        return yaml.safe_load(config_string)

    def _choose_config(self, target_env: str, target_nw: str, target_ss: str) -> Dict:
        config_data = self._read_config(target_nw, target_ss)
        return config_data[target_env]
