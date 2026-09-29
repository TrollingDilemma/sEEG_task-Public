"""Display 1/2의 touch-down event를 game action으로 변환한다."""

from collections import deque
from dataclasses import dataclass, field
from typing import Literal, Optional

from pyglet.window import mouse as pyglet_mouse

from .config import WISECOCO_DIVIDER_WIDTH, WISECOCO_MAIN_AREA_RATIO


TouchAction = Literal["turn_over", "answer_attempt"]


@dataclass
class _TouchSurface:
    side: str
    window: object
    press_positions: deque[tuple[float, float]] = field(default_factory=deque)

    def __post_init__(self) -> None:
        """PsychoPy handler를 보존하면서 pyglet press event를 즉시 수집한다."""
        self._original_on_press = self.window.winHandle.on_mouse_press

        def on_mouse_press(x, y, button, modifiers):
            self._original_on_press(x, y, button, modifiers)
            if button & pyglet_mouse.LEFT:
                scale = float(self.window.getContentScaleFactor())
                local_x = x * scale - float(self.window.size[0]) / 2
                local_y = y * scale - float(self.window.size[1]) / 2
                self.press_positions.append((local_x, local_y))

        self.window.winHandle.on_mouse_press = on_mouse_press

    def dispatch_and_pop(self) -> Optional[tuple[float, float]]:
        """대기 중인 OS/pyglet event를 처리하고 가장 오래된 press 좌표를 반환한다."""
        self.window.winHandle.dispatch_events()
        return self.press_positions.popleft() if self.press_positions else None


class TouchInputRouter:
    """두 Wisecoco Window의 press event를 현재 game action으로 판정한다."""

    def __init__(self, left_window, right_window, *, enabled: bool = True):
        self.windows = (left_window, right_window)
        self.surfaces = (
            (
                _TouchSurface("left", left_window),
                _TouchSurface("right", right_window),
            )
            if enabled
            else ()
        )

    def clear(self) -> None:
        for surface in self.surfaces:
            surface.press_positions.clear()

    @staticmethod
    def _inside_action_area(win, position: tuple[float, float]) -> bool:
        """SKY_BLUE 세로선은 제외하고 그 오른쪽부터 action 영역으로 본다."""
        x, y = position
        width = float(win.size[0])
        height = float(win.size[1])
        divider_x = -width / 2 + width * WISECOCO_MAIN_AREA_RATIO
        action_left = divider_x + WISECOCO_DIVIDER_WIDTH / 2
        return (
            action_left <= x <= width / 2
            and -height / 2 <= y <= height / 2
        )

    def poll(self, *, state: str, activated_side: Optional[str]) -> Optional[TouchAction]:
        """
        활성 side에서 발생한 touch-down 한 건을 action으로 반환한다.

        NameGame action 영역:
            SKY_BLUE 가로선 위쪽 -> turn_over
            가로선 아래쪽 -> answer_attempt
        몸으로말해요 action 영역:
            전체 -> answer_attempt
        """
        if not self.surfaces:
            for window in self.windows:
                window.winHandle.dispatch_events()
            return None

        action: Optional[TouchAction] = None
        for surface in self.surfaces:
            position = surface.dispatch_and_pop()
            if (
                action is not None
                or position is None
                or surface.side != activated_side
                or state not in {"name_game", "body_game"}
                or not self._inside_action_area(surface.window, position)
            ):
                continue

            if state == "name_game":
                half_line_width = WISECOCO_DIVIDER_WIDTH / 2
                if -half_line_width <= position[1] <= half_line_width:
                    continue
                action = "turn_over" if position[1] > 0 else "answer_attempt"
            else:
                action = "answer_attempt"
        return action
