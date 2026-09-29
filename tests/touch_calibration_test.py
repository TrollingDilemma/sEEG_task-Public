"""Touch 선택값 1/2와 Windows macro command 대응을 검증한다."""

import task.touch_calibration as calibration
from task.touch_calibration import (
    ELEVATED_MAPPING_COMMAND,
    TOUCH_MODE_BUTTONS,
    TOUCH_MODE_LABELS,
    TOUCH_MODE_USE,
    command_for_touch_mode,
)
from task.touch_input import TouchInputRouter


class _FakeHandle:
    def __init__(self):
        self.dispatch_count = 0

    def dispatch_events(self):
        self.dispatch_count += 1


class _FakeWindow:
    def __init__(self):
        self.winHandle = _FakeHandle()


def main() -> None:
    assert (TOUCH_MODE_BUTTONS, TOUCH_MODE_USE) == (1, 2)
    assert TOUCH_MODE_LABELS == (
        "1. 터치기능 미사용(버튼 사용)",
        "2. 터치기능 사용",
    )
    try:
        command_for_touch_mode(1)
    except ValueError:
        pass
    else:
        raise AssertionError("버튼 mode는 mapping command를 반환하면 안 됩니다.")
    assert command_for_touch_mode(2) == ELEVATED_MAPPING_COMMAND
    try:
        command_for_touch_mode(3)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid touch mode must raise ValueError")

    left = _FakeWindow()
    right = _FakeWindow()
    router = TouchInputRouter(left, right, enabled=False)
    assert router.poll(state="name_game", activated_side="left") is None
    assert left.winHandle.dispatch_count == 1
    assert right.winHandle.dispatch_count == 1

    launched = []
    original_select = calibration.select_touch_mode
    original_run = calibration.subprocess.run
    original_instruction = calibration._show_mapping_instruction
    try:
        calibration.subprocess.run = lambda command, check: (
            launched.append(command)
            or type("Result", (), {"returncode": 0})()
        )
        calibration._show_mapping_instruction = lambda mode: True
        calibration.select_touch_mode = lambda: 1
        assert calibration.configure_touch_before_task(3) is False
        calibration.select_touch_mode = lambda: 2
        assert calibration.configure_touch_before_task(3) is True
        calibration.select_touch_mode = lambda: 1
        assert calibration.configure_touch_before_task(1) is False
        calibration.select_touch_mode = lambda: 2
        assert calibration.configure_touch_before_task(2) is True
    finally:
        calibration.select_touch_mode = original_select
        calibration.subprocess.run = original_run
        calibration._show_mapping_instruction = original_instruction
    assert launched == [
        ELEVATED_MAPPING_COMMAND,
    ]
    print("Touch calibration test passed.")


if __name__ == "__main__":
    main()
