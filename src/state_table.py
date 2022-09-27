from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class StateTableEntry(ABC):
    @abstractmethod
    def to_dict(self) -> Dict:
        pass


class StateTable(ABC):
    def __init__(self):
        self.entries: List[StateTableEntry] = []

    @abstractmethod
    def find_entry_equiv(self, entry: StateTableEntry) -> Optional[StateTableEntry]:
        pass

    @abstractmethod
    def to_dict(self) -> Dict:
        pass
