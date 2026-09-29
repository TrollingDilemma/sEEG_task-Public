from dataclasses import dataclass
from typing import FrozenSet, Optional


@dataclass
class TurnRecord:
    index: int
    side: str                 # "left" 또는 "right"
    start_time: float
    duration: Optional[float] = None


@dataclass(frozen=True)
class InputFrame:
    keys: FrozenSet[str]
    ctrl_q: bool = False

    def has(self, key: str) -> bool:
        return key in self.keys
