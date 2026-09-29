from psychopy import core
from .models import TurnRecord


# 화면과 TTL label이 공유하는 session participant 이름.
_side_names = {"left": "", "right": ""}

def set_side_names(left_name: str, right_name: str) -> None:
    _side_names["left"] = (left_name or "").strip()
    _side_names["right"] = (right_name or "").strip()


def get_side_name(side: str) -> str:
    """입력된 참가자 이름을 반환한다. 미입력 시 빈 문자열이다."""
    return _side_names.get(side, "")


def side_display(side: str) -> str:
    """'왼쪽(민수)' 형식. 이름 미입력 시 '왼쪽'."""
    base = "왼쪽" if side == "left" else "오른쪽" if side == "right" else str(side)
    name = _side_names.get(side, "")
    return f"{base}({name})" if name else base

def start_new_turn(records: list[TurnRecord], side: str, turn_index: int, task_clock: core.Clock,) -> None:
    cumulative_time = task_clock.getTime()
    records.append(TurnRecord(index=turn_index, side=side, start_time=cumulative_time, duration=None,))

def finish_current_turn(records: list[TurnRecord], task_clock: core.Clock) -> None:
    """아직 열려 있는 마지막 turn의 duration을 확정한다."""
    if not records:
        return
    current = records[-1]
    if current.duration is None:
        current.duration = task_clock.getTime() - current.start_time

def opposite_side(side: str) -> str:
    if side == "left":
        return "right"
    if side == "right":
        return "left"
    raise ValueError(f"Unknown side: {side}")
