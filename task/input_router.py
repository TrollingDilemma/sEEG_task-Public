"""Host keyboard와 Display 1/2 touch를 한 frame 입력으로 통합한다."""

from typing import Optional

from psychopy import event
from psychopy.hardware import keyboard

from .cursor_macro import TopRowZeroEdgeDetector, move_cursor_to_window_center
from .models import InputFrame
from .touch_input import TouchInputRouter


CURSOR_MACRO_KEYS = frozenset({"0"})

KEY_LIST = [
    "right",
    "left",
    "space",
    "p",
    "r",
    "y",
    "n",
    "return",
    "backspace",
    "minus",
    "equal",
    "0",
]


def apply_game_key_bindings(host_keys: set[str], state: str) -> None:
    """상단 -/+ 물리 키를 게임별 기존 action key로 정규화한다."""
    if state == "name_game":
        if "minus" in host_keys:
            host_keys.add("space")
        if "equal" in host_keys:
            host_keys.add("return")
    elif state == "body_game" and "equal" in host_keys:
        host_keys.add("return")


class InputRouter:
    def __init__(
        self,
        operator_window,
        touch_left_window,
        touch_right_window,
        *,
        touch_enabled: bool = True,
    ):
        self.keyboard = keyboard.Keyboard()
        self.touch = TouchInputRouter(
            touch_left_window,
            touch_right_window,
            enabled=touch_enabled,
        )
        self.operator_window = operator_window
        self.top_row_zero = TopRowZeroEdgeDetector()

    def _recenter_operator_cursor(self) -> None:
        """Windows cursor를 Display 0 client area의 정중앙으로 이동한다."""
        move_cursor_to_window_center(self.operator_window)

    def poll(self, *, state: str, activated_side: Optional[str]) -> InputFrame:
        self.operator_window.winHandle.dispatch_events()
        host_keys = {
            key.name
            for key in self.keyboard.getKeys(
                keyList=KEY_LIST,
                waitRelease=False,
                clear=True,
            )
        }
        if (
            self.top_row_zero.poll()
            or host_keys.intersection(CURSOR_MACRO_KEYS)
        ):
            self._recenter_operator_cursor()
            host_keys.difference_update(CURSOR_MACRO_KEYS)
        apply_game_key_bindings(host_keys, state)
        touch_action = self.touch.poll(state=state, activated_side=activated_side)

        # 같은 frame에는 host의 P/Space/Enter가 touch보다 우선한다.
        if not host_keys.intersection({"p", "space", "return"}):
            if touch_action == "turn_over":
                host_keys.add("space")
            elif touch_action == "answer_attempt":
                host_keys.add("return")

        ctrl_q_events = event.getKeys(keyList=["q"], modifiers=True)
        ctrl_q = any(
            name == "q" and modifiers.get("ctrl", False)
            for name, modifiers in ctrl_q_events
        )
        return InputFrame(
            keys=frozenset(host_keys),
            ctrl_q=ctrl_q,
        )

    def clear(self) -> None:
        self.keyboard.clearEvents()
        self.touch.clear()
        event.clearEvents(eventType="keyboard")
