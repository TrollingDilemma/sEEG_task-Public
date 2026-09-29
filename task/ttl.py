from datetime import datetime
from time import perf_counter
from typing import Optional

from psychopy import core

from .config import (
    DATA_LINES,
    HOLD_TIME_SEC,
    LATCH_LINE,
    PULSE_WIDTH_SEC,
    SETUP_TIME_SEC,
)
from .ljm_backend import ljm


def code_to_bits(code: int) -> list[int]:
    """
    0~255 정수를 EIO0~EIO7에 대응하는 bit list로 변환한다.
    EIO0 = bit 0 = LSB = 1의 자리.
    """
    if not isinstance(code, int):
        raise TypeError("Trigger code must be an integer.")

    if code < 0 or code > 255:
        raise ValueError("Trigger code must be between 0 and 255.")

    return [(code >> bit_index) & 1 for bit_index in range(8)]

def initialize_outputs(handle):
    for line in DATA_LINES + [LATCH_LINE]:
        ljm.eWriteName(handle, line, 0)

def write_many(handle, names: list[str], values: list[float]) -> None:
    """
    LabJack register 여러 개를 한 번에 write한다.
    """
    if len(names) != len(values):
        raise ValueError("names and values must have the same length.")

    ljm.eWriteNames(handle, len(names), names, values)

def clear_all_outputs(handle) -> None:
    """
    EIO0~EIO7과 CIO0 latch를 모두 low로 초기화한다.
    """
    names = DATA_LINES + [LATCH_LINE]
    values = [0] * len(names)
    write_many(handle, names, values)

def format_trigger_timestamp(trigger_time: datetime) -> str:
    """
    Terminal에 기록할 TTL 발생 시각을 HH:MM:SS.mmm 형식으로 반환한다.

    예:
        11:57:23.987 -> 11시 57분 23.987초
    """
    return trigger_time.strftime("%H:%M:%S.%f")[:-3]

class FlipSynchronizedTrigger:
    """화면 flip에 TTL 상승 edge를 맞추고 pulse 종료는 flip 뒤에 처리한다."""

    def __init__(self, handle):
        self.handle = handle
        self._onset_monotonic: Optional[float] = None
        self._code: Optional[int] = None
        self._label = ""

    def prepare(self, win, code: int, label: str = "", sound_effect=None) -> None:
        """Data bit를 먼저 설정하고 다음 ``win.flip()``에 latch 상승을 예약한다."""
        if self._code is not None:
            raise RuntimeError("A TTL trigger is already pending for this frame.")

        bits = code_to_bits(code)
        write_many(self.handle, DATA_LINES, bits)
        core.wait(SETUP_TIME_SEC)
        self._code = code
        self._label = label

        def begin_pulse() -> None:
            # 실제 기록 event는 latch의 low -> high edge이다.
            ljm.eWriteName(self.handle, LATCH_LINE, 1)
            self._onset_monotonic = perf_counter()
            trigger_time = datetime.now()
            if sound_effect is not None:
                sound_effect.stop()
                sound_effect.play()
            timestamp_text = format_trigger_timestamp(trigger_time)
            suffix = f" | {self._label}" if self._label else ""
            print(f"[TTL] {timestamp_text} | code={self._code:3d}{suffix}")

        win.callOnFlip(begin_pulse)

    def finish(self) -> None:
        """세 창의 flip 후 pulse width를 채우고 latch와 data line을 clear한다."""
        if self._code is None:
            return
        if self._onset_monotonic is None:
            raise RuntimeError("TTL callback did not run during window flip.")

        remaining = PULSE_WIDTH_SEC - (perf_counter() - self._onset_monotonic)
        if remaining > 0:
            core.wait(remaining)
        ljm.eWriteName(self.handle, LATCH_LINE, 0)
        core.wait(HOLD_TIME_SEC)
        write_many(self.handle, DATA_LINES, [0] * len(DATA_LINES))

        self._onset_monotonic = None
        self._code = None
        self._label = ""
