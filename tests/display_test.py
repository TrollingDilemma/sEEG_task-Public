"""Display 0/1/2 물리 매핑을 본 실험 전에 눈으로 확인하는 테스트."""

import sys
from pathlib import Path

from psychopy import core, event, visual

# ``python tests/display_test.py`` 직접 실행 시에도 project package를 찾게 한다.
PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from task.displays import DISPLAY_SPECS, create_display_windows


def main() -> None:
    displays = create_display_windows()
    colors = (
        [-0.4, -0.4, 0.8],
        [-0.4, 0.8, -0.4],
        [0.8, -0.4, -0.4],
    )
    labels = (
        "DISPLAY 0\nLAPTOP / OPERATOR",
        "DISPLAY 1\nTOUCH LEFT",
        "DISPLAY 2\nTOUCH RIGHT",
    )

    try:
        for window, spec, color, label in zip(
            displays.all, DISPLAY_SPECS, colors, labels
        ):
            window.color = color
            visual.TextStim(
                window,
                text=f"{label}\n\nscreen index = {spec.screen_index}",
                color="white",
                height=48,
                units="pix",
                bold=True,
            ).draw()
        displays.flip_all()

        print("각 물리 화면의 DISPLAY 번호를 확인하세요.")
        print("종료: Esc 또는 10초 경과")
        timer = core.Clock()
        while timer.getTime() < 10.0 and "escape" not in event.getKeys():
            core.wait(0.01)
    finally:
        displays.close_all()


if __name__ == "__main__":
    main()
