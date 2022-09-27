from abc import ABC, abstractmethod
import os
import json
from typing import Dict, List, Optional


class StateTableEntry(ABC):
    """Abstract class of state table entry"""

    @abstractmethod
    def to_dict(self) -> Dict:
        """Convert self to dict"""


class StateTable(ABC):
    """Abstract class of state table"""

    def __init__(self):
        """Constructor"""
        self.table_name = "_undefined_"
        self.entries: List[StateTableEntry] = []

    @abstractmethod
    def find_entry_equiv(self, entry: StateTableEntry) -> Optional[StateTableEntry]:
        """Find an entry equivalent given one"""

    def to_dict(self) -> Dict:
        """Convert self to dict"""
        return {"table_name": self.table_name, "entries": [e.to_dict() for e in self.entries]}

    @staticmethod
    def _read_json_file(file: str) -> Dict:
        with open(os.path.expanduser(file), "r", encoding="UTF-8") as route_file:
            return json.load(route_file)
