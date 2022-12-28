from abc import ABC, abstractmethod
from typing import Dict, List, NoReturn
import re
import utility as util


class Parseable(ABC):
    """Mix-in for cisco(-like) state table which requires regexp string parsing"""

    def _match_line(self, index: int, line: str, debug=False) -> bool:
        matched = False
        for match_info in self._generate_match_info_list():
            util.debug(f"{index}: regexp={match_info['regexp']}, type={match_info['type']}", debug)
            match = re.search(match_info["regexp"], line)
            if match:
                self._add_entry_by_type(match, match_info)
                matched = True
                break
        return matched

    @staticmethod
    @abstractmethod
    def _generate_match_info_list() -> List[Dict]:
        pass

    @abstractmethod
    def _add_entry_by_type(self, match: re.Match, match_info: Dict) -> NoReturn:
        pass
