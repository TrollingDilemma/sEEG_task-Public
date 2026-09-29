"""과제 시작 전 Windows touch 사용 방식 선택과 설정 도구 실행."""

import subprocess
from typing import Optional


TOUCH_MODE_BUTTONS = 1
TOUCH_MODE_USE = 2
TOUCH_MODE_LABELS = (
    "1. 터치기능 미사용(버튼 사용)",
    "2. 터치기능 사용",
)

ELEVATED_MAPPING_COMMAND = (
    "powershell.exe",
    "-NoProfile",
    "-Command",
    "$mappingTool = Join-Path $env:WINDIR 'System32\\MultiDigiMon.exe'; "
    "try { "
    "$null = Start-Process -FilePath $mappingTool "
    "-ArgumentList '-touch' -Verb RunAs -Wait -PassThru -ErrorAction Stop; "
    # MultiDigiMon은 정상 mapping 종료 후에도 code 1을 반환할 수 있다.
    # UAC 상승 실행과 대기가 성공했다면 게임을 계속하도록 wrapper는 0을 반환한다.
    "exit 0 "
    "} catch { Write-Error $_; exit 2 }",
)


def command_for_touch_mode(mode: int) -> tuple[str, ...]:
    """터치 사용 mode의 Windows 물리 display mapping command를 반환한다."""
    if mode == TOUCH_MODE_USE:
        return ELEVATED_MAPPING_COMMAND
    raise ValueError(f"물리 mapping을 실행하지 않는 touch mode: {mode}")


def select_touch_mode() -> Optional[int]:
    """게임 시작 전 dropdown 선택값을 1/2로 반환하고 Cancel은 None으로 반환한다."""
    from psychopy import gui

    dialog = gui.Dlg(title="터치기능 설정")
    dialog.addText("게임 시작 전 터치기능 사용 여부를 선택하세요.")
    dialog.addField(
        "선택",
        initial=TOUCH_MODE_LABELS[0],
        choices=list(TOUCH_MODE_LABELS),
    )
    dialog.show()
    if not dialog.OK:
        return None
    selected_label = str(dialog.data[0])
    return (
        TOUCH_MODE_BUTTONS
        if selected_label == TOUCH_MODE_LABELS[0]
        else TOUCH_MODE_USE
    )


def _show_mapping_instruction(mode: int) -> bool:
    """물리 mapping wizard 실행 전에 host에게 작업을 안내한다."""
    from psychopy import gui

    dialog = gui.Dlg(title="디스플레이 mapping 안내")
    dialog.addText("물리 mapping을 완료하십시오.")
    dialog.show()
    return bool(dialog.OK)


def configure_touch_before_task(connected_screen_count: int) -> Optional[bool]:
    """
    선택창과 Windows 설정 macro를 실행한다.

    반환:
        False -> 선택값 1, 물리 버튼 사용 / touch input 비활성
        True  -> 선택값 2, touch input 활성
        None  -> 사용자가 취소하거나 Windows 도구 실행 실패
    """
    mode = select_touch_mode()
    if mode is None:
        return None
    touch_enabled = mode == TOUCH_MODE_USE
    if mode == TOUCH_MODE_BUTTONS:
        print("[INFO] Touch mode=1 | 물리 mapping 미실행 | 물리 버튼 사용")
        return False
    if connected_screen_count < 3:
        print(
            "[MOCK-UP] 물리 display가 3개 미만이므로 mapping 도구를 건너뛰고 "
            "노트북 DISPLAY 0/1/2 3분할 모드를 사용합니다."
        )
        return touch_enabled
    if not _show_mapping_instruction(mode):
        return None
    command = command_for_touch_mode(mode)
    try:
        # mapping wizard가 끝날 때까지 기다린 뒤 게임 준비를 계속한다.
        result = subprocess.run(command, check=False)
    except OSError as exc:
        print(f"[ERROR] Windows display mapping 도구를 열지 못했습니다: {exc}")
        return None
    if result.returncode != 0:
        print(f"[취소] Display mapping이 완료되지 않았습니다: code={result.returncode}")
        return None
    input_label = "touch input 활성" if touch_enabled else "물리 버튼 사용"
    print(f"[INFO] Touch mode={mode} | {input_label}")
    return touch_enabled


def main() -> None:
    # 독립 실행에서도 선택값 2만 물리 mapping을 실행한다.
    result = configure_touch_before_task(3)
    if result is None:
        print("[취소] Touch screen 설정을 완료하지 않았습니다.")


if __name__ == "__main__":
    main()
