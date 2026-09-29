"""PsychoPy의 세 물리 디스플레이 창을 생성하고 함께 관리한다."""

from dataclasses import dataclass

from psychopy import visual

from .config import (
    COLOR_SPACE,
    DISPLAY_0_INDEX,
    DISPLAY_0_SIZE,
    DISPLAY_1_INDEX,
    DISPLAY_1_SIZE,
    DISPLAY_2_INDEX,
    DISPLAY_2_SIZE,
    FULLSCREEN,
    GRAY,
    WINDOW_BACKEND,
)


@dataclass(frozen=True)
class DisplaySpec:
    """하나의 PsychoPy 창과 물리 디스플레이 사이의 고정 매핑."""

    role: str
    screen_index: int
    size: tuple[int, int]


DISPLAY_SPECS = (
    DisplaySpec("operator", DISPLAY_0_INDEX, DISPLAY_0_SIZE),
    DisplaySpec("touch_left", DISPLAY_1_INDEX, DISPLAY_1_SIZE),
    DisplaySpec("touch_right", DISPLAY_2_INDEX, DISPLAY_2_SIZE),
)


def _get_pyglet_screens():
    """현재 OS에서 확장 데스크톱으로 인식되는 물리 screen 목록을 반환한다."""
    try:
        from pyglet import display as pyglet_display
        return pyglet_display.get_display().get_screens()
    except ImportError:
        # pyglet 1.x compatibility
        from pyglet import canvas
        return canvas.get_display().get_screens()


def get_connected_screen_count() -> int:
    """노트북 화면을 포함하여 OS가 인식한 screen 개수를 반환한다."""
    return len(_get_pyglet_screens())


@dataclass
class DisplayWindows:
    """Display 0/1/2에 대응하는 세 PsychoPy Window."""

    operator: visual.Window
    touch_left: visual.Window
    touch_right: visual.Window

    @property
    def all(self) -> tuple[visual.Window, visual.Window, visual.Window]:
        return self.operator, self.touch_left, self.touch_right

    def flip_all(self) -> None:
        """참가자 화면을 우선한 뒤 operator 화면을 표시한다."""
        for window in (self.touch_left, self.touch_right, self.operator):
            window.flip()

    def close_all(self) -> None:
        """일부 창의 종료가 실패해도 나머지 창까지 모두 닫는다."""
        for window in reversed(self.all):
            try:
                window.close()
            except Exception:
                pass


def _create_window(
    spec: DisplaySpec,
    *,
    size: tuple[int, int] | None = None,
    screen_index: int | None = None,
    pos: tuple[int, int] | None = None,
    fullscr: bool = FULLSCREEN,
    allow_gui: bool = False,
    title: str | None = None,
    wait_blanking: bool = True,
) -> visual.Window:
    return visual.Window(
        size=size or spec.size,
        screen=spec.screen_index if screen_index is None else screen_index,
        pos=pos,
        name=spec.role,
        title=title or f"sEEG task - {spec.role}",
        color=GRAY,
        colorSpace=COLOR_SPACE,
        units="pix",
        fullscr=fullscr,
        allowGUI=allow_gui,
        winType=WINDOW_BACKEND,
        waitBlanking=wait_blanking,
    )


def create_display_windows(*, single_display_mockup: bool = False) -> DisplayWindows:
    """실물 3-screen 또는 노트북 횡 3분할 mock-up 창을 생성한다."""
    created: list[visual.Window] = []
    try:
        if single_display_mockup:
            laptop_screen = _get_pyglet_screens()[0]
            screen_width = int(laptop_screen.width)
            screen_height = int(laptop_screen.height)
            outer_margin = max(4, round(screen_width * 0.006))
            slot_gap = max(4, round(screen_width * 0.006))
            top_margin = max(35, round(screen_height * 0.045))
            bottom_margin = max(55, round(screen_height * 0.075))
            usable_width = screen_width - 2 * outer_margin - 2 * slot_gap
            usable_height = max(80, screen_height - top_margin - bottom_margin)
            slot_width = max(80, usable_width // 3)
            for display_number, spec in enumerate(DISPLAY_SPECS):
                # 각 1/3 슬롯 안에서 원본 display 종횡비를 유지한다.
                aspect_ratio = (
                    screen_width / screen_height
                    if display_number == 0
                    else spec.size[0] / spec.size[1]
                )
                width = min(slot_width, int(usable_height * aspect_ratio))
                height = min(usable_height, int(width / aspect_ratio))
                slot_left = outer_margin + display_number * (slot_width + slot_gap)
                left = slot_left + (slot_width - width) // 2
                top = top_margin + (usable_height - height) // 2
                created.append(
                    _create_window(
                        spec,
                        size=(width, height),
                        screen_index=0,
                        pos=(left, top),
                        fullscr=False,
                        allow_gui=True,
                        title=f"DISPLAY {display_number} | {spec.role}",
                        # 한 물리 screen에서 세 번의 VSync 대기가 발생하지 않게 한다.
                        wait_blanking=False,
                    )
                )
        else:
            physical_screens = _get_pyglet_screens()
            for spec in DISPLAY_SPECS:
                physical_screen = physical_screens[spec.screen_index]
                created.append(
                    _create_window(
                        spec,
                        size=(
                            int(physical_screen.width),
                            int(physical_screen.height),
                        ),
                        fullscr=True,
                    )
                )
        return DisplayWindows(*created)
    except Exception:
        for window in reversed(created):
            try:
                window.close()
            except Exception:
                pass
        raise
