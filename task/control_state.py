"""Verbal/Nonverbal Control의 문장과 입력 전이를 관리한다."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import (
    CODE_NONVERBAL_CONTROL_CANCEL,
    CODE_NONVERBAL_CONTROL_FINISH,
    CODE_NONVERBAL_CONTROL_START,
    CODE_VERBAL_CONTROL_CANCEL,
    CODE_VERBAL_CONTROL_FINISH,
    CODE_VERBAL_CONTROL_NEXT,
    CODE_VERBAL_CONTROL_PREVIOUS,
    CODE_VERBAL_CONTROL_START,
    VERBAL_CONTROL_SCRIPT_PATH,
)
from .models import InputFrame


CONTROL_STATES = frozenset({
    "verbal_control_confirm",
    "nonverbal_control_confirm",
    "verbal_control",
    "nonverbal_control",
})


def _load_verbal_sentences(path: Path) -> tuple[str, ...]:
    if not path.is_file():
        raise FileNotFoundError(f"Verbal Control script를 찾을 수 없습니다: {path}")
    sentences = tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    )
    if len(sentences) != 10:
        raise ValueError(
            "Verbal Control script에는 비어 있지 않은 문장이 정확히 "
            f"10줄 있어야 합니다: {path} (현재 {len(sentences)}줄)"
        )
    return sentences


@dataclass(frozen=True)
class ControlStep:
    next_state: Optional[str] = None
    code: Optional[int] = None
    label: str = ""
    clear_inputs: bool = False
    start_session_timer: bool = False
    enter_control_finish: bool = False


class ControlState:
    """Control 선택 cursor와 VC 문장 index를 소유한다."""

    def __init__(self, script_path: Path = VERBAL_CONTROL_SCRIPT_PATH):
        self.sentences = _load_verbal_sentences(script_path)
        self.confirm_cursor = 1
        self.sentence_index = 0

    def reset(self) -> None:
        self.confirm_cursor = 1
        self.sentence_index = 0

    @property
    def sentence(self) -> str:
        return self.sentences[self.sentence_index]

    def step(self, state: str, inputs: InputFrame) -> Optional[ControlStep]:
        if state == "verbal_control_confirm":
            return self._step_verbal_confirm(inputs)
        if state == "nonverbal_control_confirm":
            return self._step_nonverbal_confirm(inputs)
        if state == "verbal_control":
            return self._step_verbal(inputs)
        if state == "nonverbal_control":
            return self._step_nonverbal(inputs)
        return None

    def _step_verbal_confirm(self, inputs: InputFrame) -> Optional[ControlStep]:
        if inputs.has("left"):
            self.confirm_cursor = 0
            return ControlStep(clear_inputs=True)
        if inputs.has("right"):
            self.confirm_cursor = 1
            return ControlStep(clear_inputs=True)
        if not inputs.has("return"):
            return None
        if self.confirm_cursor == 0:
            self.sentence_index = 0
            return ControlStep(
                next_state="verbal_control",
                code=CODE_VERBAL_CONTROL_START,
                label="Enter / Verbal Control 시작 | i=1",
                clear_inputs=True,
                start_session_timer=True,
            )
        return ControlStep(
            next_state="select_game",
            code=CODE_VERBAL_CONTROL_CANCEL,
            label="Enter / Verbal Control 진행 안 함 -> 게임 선택",
            clear_inputs=True,
        )

    def _step_verbal(self, inputs: InputFrame) -> Optional[ControlStep]:
        if inputs.has("space"):
            if self.sentence_index == len(self.sentences) - 1:
                return ControlStep(
                    next_state="control_finish",
                    code=CODE_VERBAL_CONTROL_FINISH,
                    label="Space / Verbal Control 마지막 문장 완료 -> control 종료화면 | i=10",
                    clear_inputs=True,
                    enter_control_finish=True,
                )
            self.sentence_index += 1
            return ControlStep(
                code=CODE_VERBAL_CONTROL_NEXT,
                label=f"Space / Verbal Control 다음 문장 | i={self.sentence_index + 1}",
                clear_inputs=True,
            )
        if inputs.has("backspace"):
            self.sentence_index = max(0, self.sentence_index - 1)
            return ControlStep(
                code=CODE_VERBAL_CONTROL_PREVIOUS,
                label=(
                    "Backspace / Verbal Control 이전 문장 | "
                    f"i={self.sentence_index + 1}"
                ),
                clear_inputs=True,
            )
        return None

    def _step_nonverbal_confirm(self, inputs: InputFrame) -> Optional[ControlStep]:
        if inputs.has("left"):
            self.confirm_cursor = 0
            return ControlStep(clear_inputs=True)
        if inputs.has("right"):
            self.confirm_cursor = 1
            return ControlStep(clear_inputs=True)
        if not inputs.has("return"):
            return None
        if self.confirm_cursor == 0:
            return ControlStep(
                next_state="nonverbal_control",
                code=CODE_NONVERBAL_CONTROL_START,
                label="Enter / Nonverbal Control 시작",
                clear_inputs=True,
                start_session_timer=True,
            )
        return ControlStep(
            next_state="select_game",
            code=CODE_NONVERBAL_CONTROL_CANCEL,
            label="Enter / Nonverbal Control 진행 안 함 -> 게임 선택",
            clear_inputs=True,
        )

    @staticmethod
    def _step_nonverbal(inputs: InputFrame) -> Optional[ControlStep]:
        if not inputs.has("space"):
            return None
        return ControlStep(
            next_state="control_finish",
            code=CODE_NONVERBAL_CONTROL_FINISH,
            label="Space / Nonverbal Control 종료 -> control 종료화면",
            clear_inputs=True,
            enter_control_finish=True,
        )
