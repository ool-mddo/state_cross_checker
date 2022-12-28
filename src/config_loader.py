import os
from typing import Dict
import yaml
from jinja2 import Environment, FileSystemLoader
import utility as util


# pylint: disable=too-many-instance-attributes
class ConfigLoader:
    def __init__(
        self, config_file: str, src_env: str, dst_env: str, network: str, src_ss: str, dst_ss: str, debug=False
    ):
        self.config_file = os.path.expanduser(config_file)
        self.src_env = src_env
        self.dst_env = dst_env
        self.network = network
        self.src_ss = src_ss  # source snapshot
        self.dst_ss = dst_ss  # destination snapshot
        self.debug = debug
        self._load_config()

    def _load_config(self):

        if not os.path.exists(self.config_file):
            util.error_exit(f"config file: {self.config_file} is not found")

        config_data = self._read_config(self.network, self.src_ss)
        self.original_node_params = config_data["original_node_params"]
        self.src_config = self._choose_config(self.src_env, self.src_ss)
        self.dst_config = self._choose_config(self.dst_env, self.dst_ss)

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

    def _choose_config(self, target_env: str, target_ss: str) -> Dict:
        config_data = self._read_config(self.network, target_ss)
        return config_data[target_env]
