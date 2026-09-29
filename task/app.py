"""장비 setup과 task의 최상위 poll-step-render loop."""

import sys
import traceback

from psychopy import core

from .config import (
    BODY_EXPLAIN_DURATION_SEC,
    BODY_SOUND_PATH,
    CONNECTION_TYPE,
    DEVICE_TYPE,
    IDENTIFIER,
)
from .display_router import DisplayRouter
from .displays import create_display_windows, get_connected_screen_count
from .game_state import GameState
from .input_router import InputRouter
from .ljm_backend import ljm
from .sounds import create_state_transition_tone, load_sound_effect
from .state_utils import set_side_names
from .ttl import FlipSynchronizedTrigger, clear_all_outputs, initialize_outputs
from .touch_calibration import configure_touch_before_task


def confirm_proceed_without_labjack(_exc, _mockup_description: str) -> bool:
    """LabJack 연결 실패 시 실제 timing MOCK 진행 여부를 확인한다."""
    try:
        from psychopy import gui
        dlg = gui.Dlg(title="⚠ LabJack 연결 실패")
        dlg.addText(
            "LabJack T4에 연결하지 못했습니다. "
            "MOCK-UP을 시작하려면 OK, 종료하려면 Cancel."
        )
        dlg.show()
        return bool(dlg.OK)
    except Exception as dialog_exc:
        print(f"[경고] 확인 dialog를 띄우지 못했습니다: {dialog_exc}")
        print("[종료] 안전을 위해 프로그램을 종료합니다.")
        return False


def ask_player_names() -> None:
    """세션 시작 시 왼쪽/오른쪽 참가자 이름을 입력받는다."""
    left_name = ""
    right_name = ""
    try:
        from psychopy import gui
        dlg = gui.Dlg(title="참가자 이름 입력")
        dlg.addText("각 참가자의 이름을 입력하세요. (비워두면 왼쪽/오른쪽으로 표기)")
        dlg.addField("왼쪽 사람 이름")
        dlg.addField("오른쪽 사람 이름")
        dlg.show()
        if dlg.OK:
            left_name = str(dlg.data[0] or "")
            right_name = str(dlg.data[1] or "")
    except Exception as exc:
        print(f"[경고] 이름 입력 dialog 실패 (기본 표기 사용): {exc}")
    set_side_names(left_name, right_name)
    print(
        f"[INFO] 참가자 | 왼쪽: {left_name or '(미입력)'} | "
        f"오른쪽: {right_name or '(미입력)'}"
    )


def _open_labjack_or_mock(connected_screen_count: int):
    """연결 조건을 검증하고 (handle, single_display_mockup)을 반환한다."""
    try:
        handle = ljm.openS(DEVICE_TYPE, CONNECTION_TYPE, IDENTIFIER)
        print("[OK] LabJack 연결됨.")
        if connected_screen_count < 3:
            print(
                "[MOCK-UP] LabJack은 연결되었지만 물리 display가 3개 미만입니다. "
                "노트북 DISPLAY 0/1/2 3분할 화면으로 진행합니다. "
                f"인식된 screen 수={connected_screen_count}"
            )
            return handle, True
        return handle, False
    except Exception as exc:
        print("\n" + "=" * 60)
        print("[경고] LabJack 연결 실패!")
        print(f"[경고] 원인: {exc}")
        print("=" * 60)
        if connected_screen_count < 3:
            single_display_mockup = True
            description = (
                "물리 display가 3개 미만입니다. "
                "노트북 화면에 DISPLAY 0/1/2 창을 횡방향 3분할합니다."
            )
        elif connected_screen_count >= 3:
            single_display_mockup = False
            description = (
                "Wisecoco display 2대가 모두 연결되었습니다. "
                "DISPLAY 0/1/2를 각 물리 화면에 출력합니다."
            )
        if not confirm_proceed_without_labjack(exc, description):
            print("[종료] 사용자가 LabJack 없이 진행을 취소했습니다.")
            return None, False
        ljm.use_mock()
        handle = ljm.openS(DEVICE_TYPE, CONNECTION_TYPE, IDENTIFIER)
        print(f"[MOCK-UP] {description} 실제 TTL 없음.")
        return handle, single_display_mockup


def run_task() -> None:
    print("====================================")
    print("NatusQuantum TTL GUI task")
    print("====================================")
    print("현재 실행 중인 Python:")
    print(sys.executable)
    try:
        connected_screen_count = get_connected_screen_count()
    except Exception as exc:
        print(f"[종료] 연결된 display 수를 확인하지 못했습니다: {exc}")
        return

    touch_enabled = configure_touch_before_task(connected_screen_count)
    if touch_enabled is None:
        print("[종료] Touch 설정 선택 또는 mapping 취소로 session을 종료합니다.")
        return
    ask_player_names()

    handle, single_display_mockup = _open_labjack_or_mock(connected_screen_count)
    if handle is None:
        return

    display_windows = None
    try:
        initialize_outputs(handle)
        clear_all_outputs(handle)
        display_windows = create_display_windows(
            single_display_mockup=single_display_mockup
        )
        body_sound = load_sound_effect(BODY_SOUND_PATH, "몸으로말해요 효과음")
        state_transition_sound = create_state_transition_tone()
        game = GameState(
            core.Clock(),
            BODY_EXPLAIN_DURATION_SEC,
            state_transition_sound=state_transition_sound,
        )
        inputs = InputRouter(
            display_windows.operator,
            display_windows.touch_left,
            display_windows.touch_right,
            touch_enabled=touch_enabled,
        )
        displays = DisplayRouter(
            display_windows,
            FlipSynchronizedTrigger(handle),
            touch_enabled=touch_enabled,
        )

        displays.render(game)
        displays.present(game.initial_result().trigger)

        while True:
            input_frame = inputs.poll(
                state=game.state,
                activated_side=game.current_side,
            )
            result = game.step(input_frame, body_sound=body_sound)
            if result.clear_inputs:
                inputs.clear()
            displays.render(game)
            displays.present(result.trigger)
            if result.exit_after_flip:
                break
            core.wait(0.001)

    except Exception:
        print("\n[ERROR] task.app.run_task 실행 중 예외발생")
        traceback.print_exc()
        raise
    finally:
        print("\nClearing outputs and closing LabJack...")
        try:
            clear_all_outputs(handle)
        except Exception as exc:
            print("Failed to clear outputs:", exc)
        try:
            ljm.close(handle)
        except Exception as exc:
            print("Failed to close LabJack:", exc)
        if display_windows is not None:
            display_windows.close_all()
