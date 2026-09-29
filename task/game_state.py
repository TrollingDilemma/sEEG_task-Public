"""게임 state, timer, turn record 및 event-code 전이를 관리한다."""

from dataclasses import dataclass
from typing import Optional

from psychopy import core

from .config import (
    CODE_BODY_AUTO_TO_LEFT,
    CODE_BODY_AUTO_TO_RIGHT,
    CODE_BODY_FIRST_LEFT,
    CODE_BODY_FIRST_RIGHT,
    CODE_BODY_GAME_START,
    CODE_BODY_PASS_LEFT,
    CODE_BODY_PASS_RIGHT,
    CODE_BODY_TRY_CANCEL,
    CODE_BODY_TRY_LEFT,
    CODE_BODY_TRY_NO,
    CODE_BODY_TRY_RIGHT,
    CODE_BODY_TRY_YES,
    CODE_EXIT_NO,
    CODE_EXIT_REQUEST,
    CODE_EXIT_YES,
    CODE_NAME_FIRST_LEFT,
    CODE_NAME_FIRST_RIGHT,
    CODE_NAME_GAME_START,
    CODE_NAME_PASS_LEFT,
    CODE_NAME_PASS_RIGHT,
    CODE_NAME_TRY_CANCEL,
    CODE_NAME_TRY_LEFT,
    CODE_NAME_TRY_NO,
    CODE_NAME_TRY_RIGHT,
    CODE_NAME_TRY_YES,
    CODE_NAME_TURN_TO_LEFT,
    CODE_NAME_TURN_TO_RIGHT,
    CODE_RESET_BODY_ORDER,
    CODE_RESET_BODY_START,
    CODE_RESET_EXIT,
    CODE_RESET_NAME_ORDER,
    CODE_RESET_NAME_START,
    CODE_SELECT_BODYGAME,
    CODE_SELECT_GAME_ENTER,
    CODE_SELECT_NAMEGAME,
    CODE_NONVERBAL_CONTROL_CONFIRM,
    CODE_NONVERBAL_CONTROL_GAME_SELECT,
    CODE_NONVERBAL_CONTROL_RETURN,
    CODE_VERBAL_CONTROL_CONFIRM,
    CODE_VERBAL_CONTROL_GAME_SELECT,
    CODE_VERBAL_CONTROL_RETURN,
    STATE_TRANSITION_SOUND_CODES,
)
from .control_state import CONTROL_STATES, ControlState
from .models import InputFrame, TurnRecord
from .state_utils import (
    finish_current_turn,
    opposite_side,
    side_display,
    start_new_turn,
)
from .word_state import WordState
from .words import list_available_word_lists


ACTIVE_GAME_STATES = frozenset({"name_game", "body_game"})
WORD_LIST_STATES = frozenset({"name_word_list", "body_word_list"})
HOST_MANIPULATION_STATES = frozenset(
    {
        "select_game",
        "verbal_control_confirm",
        "nonverbal_control_confirm",
        "name_order",
        "body_order",
        "name_word_list",
        "body_word_list",
        "name_start_confirm",
        "body_start_confirm",
        "control_finish",
        "exit_confirm",
    }
)


@dataclass(frozen=True)
class TriggerEvent:
    code: int
    label: str
    sound_effect: object | None = None


@dataclass(frozen=True)
class StepResult:
    trigger: Optional[TriggerEvent] = None
    exit_after_flip: bool = False
    clear_inputs: bool = False


class GameState:
    def __init__(
        self,
        task_clock: core.Clock,
        body_duration: float,
        *,
        state_transition_sound=None,
    ):
        self.clock = task_clock
        self.body_duration = body_duration
        self.words = WordState()
        self.control = ControlState()
        self.state_transition_sound = state_transition_sound
        self.available_word_lists = list_available_word_lists()
        self.state = "select_game"
        self.previous_state_before_exit: Optional[str] = None
        self.exit_confirm_enter_time: Optional[float] = None
        self.first_side: Optional[str] = None
        self.current_side: Optional[str] = None
        self.try_answering_return_state: Optional[str] = None
        self.try_answering_enter_time: Optional[float] = None
        self.select_cursor = 0
        self.order_cursor = 0
        self.try_cursor = 1
        self.exit_cursor = 1
        self.control_finish_return_state: Optional[str] = None
        self.control_finish_enter_time: Optional[float] = None
        self.word_list_cursor = 0
        self.turn_index = 0
        self.records: list[TurnRecord] = []
        self.word_outcome_records: dict[str, list[str]] = {
            "left": [],
            "right": [],
        }
        self.body_phase_start_time = 0.0
        self.session_paused_duration = 0.0

    @staticmethod
    def initial_result() -> StepResult:
        return StepResult(
            TriggerEvent(CODE_SELECT_GAME_ENTER, "세션 시작 / 게임 선택 진입")
        )

    def _result(
        self,
        code: int,
        label: str,
        *,
        sound_effect=None,
        exit_after_flip: bool = False,
    ) -> StepResult:
        if sound_effect is None and code in STATE_TRANSITION_SOUND_CODES:
            sound_effect = self.state_transition_sound
        return StepResult(
            TriggerEvent(code, label, sound_effect),
            exit_after_flip=exit_after_flip,
            clear_inputs=True,
        )

    @staticmethod
    def _word_change_label(side: str, following: str) -> str:
        """TTL 설명에 참가자와 새 제시어만 기록한다."""
        return f"{side_display(side)} 단어: {following}"

    def _reset_common_context(self) -> None:
        self.first_side = None
        self.current_side = None
        self.try_answering_return_state = None
        self.try_answering_enter_time = None
        self.turn_index = 0
        self.records = []
        self.word_outcome_records = {"left": [], "right": []}
        self.body_phase_start_time = 0.0
        self.session_paused_duration = 0.0
        self.words.regenerate()
        self.select_cursor = 0
        self.order_cursor = 0
        self.try_cursor = 1
        self.exit_cursor = 1
        self.control_finish_return_state = None
        self.control_finish_enter_time = None
        self.control.reset()
        self.word_list_cursor = 0

    def _pause_active_timers(self, paused_duration: float) -> None:
        if self.previous_state_before_exit == "body_game":
            self.body_phase_start_time += paused_duration
        if (
            self.previous_state_before_exit == "try_answering"
            and self.try_answering_enter_time is not None
        ):
            self.try_answering_enter_time += paused_duration
        if self.previous_state_before_exit in ACTIVE_GAME_STATES and self.records:
            record = self.records[-1]
            if record.duration is None:
                record.start_time += paused_duration

    def _pause_answer_timer(self, return_state: Optional[str]) -> None:
        if self.try_answering_enter_time is None:
            return
        paused_duration = self.clock.getTime() - self.try_answering_enter_time
        if return_state == "body_game":
            self.body_phase_start_time += paused_duration
        if return_state in ACTIVE_GAME_STATES and self.records:
            record = self.records[-1]
            if record.duration is None:
                record.start_time += paused_duration
        self.try_answering_enter_time = None

    def _start_game(self, game: str) -> None:
        if self.first_side is None:
            raise ValueError(f"{game}_start_confirm entered without first_side")
        self.words.regenerate()
        self.clock.reset()
        self.session_paused_duration = 0.0
        self.current_side = self.first_side
        self.records = []
        self.word_outcome_records = {"left": [], "right": []}
        self.turn_index = 1
        start_new_turn(self.records, self.current_side, self.turn_index, self.clock)
        if game == "body":
            self.body_phase_start_time = self.clock.getTime()

    def _switch_turn(self) -> None:
        finish_current_turn(self.records, self.clock)
        self.current_side = opposite_side(self.current_side)
        self.turn_index += 1
        start_new_turn(self.records, self.current_side, self.turn_index, self.clock)

    def step(self, inputs: InputFrame, *, body_sound=None) -> StepResult:
        """입력 한 frame을 처리하고 최대 한 개의 TTL event를 반환한다."""
        if inputs.ctrl_q and self.state != "exit_confirm":
            self.previous_state_before_exit = self.state
            self.exit_confirm_enter_time = self.clock.getTime()
            self.exit_cursor = 1
            self.state = "exit_confirm"
            return self._result(CODE_EXIT_REQUEST, "Ctrl+Q / 종료확인진입")

        if inputs.has("p") and self.state in ACTIVE_GAME_STATES:
            if self.current_side in {"left", "right"}:
                passed_word, following, index = self.words.proceed(self.current_side)
                self.word_outcome_records[self.current_side].append(
                    f"{passed_word}(PASS)"
                )
                if self.state == "name_game":
                    code = (
                        CODE_NAME_PASS_LEFT
                        if self.current_side == "left"
                        else CODE_NAME_PASS_RIGHT
                    )
                else:
                    code = (
                        CODE_BODY_PASS_LEFT
                        if self.current_side == "left"
                        else CODE_BODY_PASS_RIGHT
                    )
                label = (
                    f"P / {self.state} {self.current_side} PASS | "
                    f"{self._word_change_label(self.current_side, following)} "
                    f"({index + 1}/{len(self.words.arrays[self.current_side])})"
                )
                return self._result(code, label)

        if inputs.has("r"):
            if self.state == "name_order":
                self._reset_common_context()
                self.state = "select_game"
                return self._result(CODE_RESET_NAME_ORDER, "R / name_order -> 게임선택")
            if self.state == "body_order":
                self._reset_common_context()
                self.state = "select_game"
                return self._result(CODE_RESET_BODY_ORDER, "R / body_order -> 게임선택")
            if self.state == "name_start_confirm":
                self.first_side = self.current_side = None
                self.records = []
                self.word_outcome_records = {"left": [], "right": []}
                self.turn_index = 0
                self.state = "name_order"
                return self._result(CODE_RESET_NAME_START, "R / name_start_confirm -> 순서재설정")
            if self.state == "body_start_confirm":
                self.first_side = self.current_side = None
                self.records = []
                self.word_outcome_records = {"left": [], "right": []}
                self.turn_index = 0
                self.state = "body_order"
                return self._result(CODE_RESET_BODY_START, "R / body_start_confirm -> 순서재설정")
            if self.state == "name_word_list":
                self.state = "name_order"
                return self._result(CODE_RESET_NAME_START, "R / name_word_list -> 순서재설정")
            if self.state == "body_word_list":
                self.state = "body_order"
                return self._result(CODE_RESET_BODY_START, "R / body_word_list -> 순서재설정")

        if self.state in WORD_LIST_STATES:
            if inputs.has("left"):
                self.word_list_cursor = (
                    self.word_list_cursor - 1
                ) % len(self.available_word_lists)
                return StepResult(clear_inputs=True)
            if inputs.has("right"):
                self.word_list_cursor = (
                    self.word_list_cursor + 1
                ) % len(self.available_word_lists)
                return StepResult(clear_inputs=True)
            if inputs.has("return"):
                selected = self.available_word_lists[self.word_list_cursor]
                self.words.select(selected)
                self.state = (
                    "name_start_confirm"
                    if self.state == "name_word_list"
                    else "body_start_confirm"
                )
                return StepResult(clear_inputs=True)

        if self.state == "select_game":
            if inputs.has("left"):
                self.select_cursor = (self.select_cursor - 1) % 4
            elif inputs.has("right"):
                self.select_cursor = (self.select_cursor + 1) % 4
            elif inputs.has("return"):
                self.order_cursor = 0
                if self.select_cursor == 0:
                    self.control.reset()
                    self.state = "verbal_control_confirm"
                    return self._result(
                        CODE_VERBAL_CONTROL_CONFIRM,
                        "Enter / Verbal Control 진행 확인 진입",
                    )
                if self.select_cursor == 1:
                    self.control.reset()
                    self.state = "nonverbal_control_confirm"
                    return self._result(
                        CODE_NONVERBAL_CONTROL_CONFIRM,
                        "Enter / Nonverbal Control 진행 확인 진입",
                    )
                if self.select_cursor == 2:
                    self.state = "name_order"
                    return self._result(CODE_SELECT_NAMEGAME, "Enter / NameGame 선택")
                self.state = "body_order"
                return self._result(CODE_SELECT_BODYGAME, "Enter / 몸으로말해요 선택")

        elif self.state in CONTROL_STATES:
            previous_state = self.state
            control_step = self.control.step(self.state, inputs)
            if control_step is None:
                return StepResult()
            if control_step.start_session_timer:
                self.clock.reset()
                self.session_paused_duration = 0.0
            if control_step.enter_control_finish:
                self.control_finish_return_state = previous_state
                self.control_finish_enter_time = self.clock.getTime()
            if control_step.next_state is not None:
                self.state = control_step.next_state
                if self.state == "select_game":
                    self.select_cursor = 0
            if control_step.code is None:
                return StepResult(clear_inputs=control_step.clear_inputs)
            return self._result(control_step.code, control_step.label)

        elif self.state in {"name_order", "body_order"}:
            if inputs.has("left"):
                self.order_cursor = 0
            elif inputs.has("right"):
                self.order_cursor = 1
            elif inputs.has("return"):
                self.first_side = "left" if self.order_cursor == 0 else "right"
                if self.state == "name_order":
                    self.state = "name_word_list"
                    self.word_list_cursor = 0
                    code = (
                        CODE_NAME_FIRST_LEFT
                        if self.first_side == "left"
                        else CODE_NAME_FIRST_RIGHT
                    )
                else:
                    self.state = "body_word_list"
                    self.word_list_cursor = 0
                    code = (
                        CODE_BODY_FIRST_LEFT
                        if self.first_side == "left"
                        else CODE_BODY_FIRST_RIGHT
                    )
                return self._result(
                    code,
                    f"Enter / {side_display(self.first_side)} 먼저 시작",
                )

        elif self.state == "name_start_confirm" and inputs.has("return"):
            self._start_game("name")
            self.state = "name_game"
            word_changes = " | ".join(
                self._word_change_label(side, self.words.current(side))
                for side in ("left", "right")
            )
            return self._result(
                CODE_NAME_GAME_START,
                f"Enter / NameGame 본게임 시작 | {word_changes}",
            )

        elif self.state == "body_start_confirm" and inputs.has("return"):
            self._start_game("body")
            self.state = "body_game"
            word_changes = " | ".join(
                self._word_change_label(side, self.words.current(side))
                for side in ("left", "right")
            )
            return self._result(
                CODE_BODY_GAME_START,
                f"Enter / 몸으로말해요 본게임 시작 | {word_changes}",
            )

        elif self.state == "name_game":
            if inputs.has("return"):
                code = (
                    CODE_NAME_TRY_LEFT
                    if self.current_side == "left"
                    else CODE_NAME_TRY_RIGHT
                )
                self.try_answering_return_state = "name_game"
                self.try_answering_enter_time = self.clock.getTime()
                self.try_cursor = 1
                self.state = "try_answering"
                return self._result(
                    code,
                    f"Enter/터치: name {side_display(self.current_side)} 정답시도",
                )
            if inputs.has("space"):
                self._switch_turn()
                code = (
                    CODE_NAME_TURN_TO_RIGHT
                    if self.current_side == "right"
                    else CODE_NAME_TURN_TO_LEFT
                )
                return self._result(code, f"Spacebar / 차례넘김 ({self.current_side})")

        elif self.state == "body_game":
            now = self.clock.getTime()
            if inputs.has("return"):
                code = (
                    CODE_BODY_TRY_LEFT
                    if self.current_side == "left"
                    else CODE_BODY_TRY_RIGHT
                )
                self.try_answering_return_state = "body_game"
                self.try_answering_enter_time = now
                self.try_cursor = 1
                self.state = "try_answering"
                return self._result(
                    code,
                    f"Enter/터치: body {side_display(self.current_side)} 정답시도",
                )
            if now - self.body_phase_start_time >= self.body_duration:
                self._switch_turn()
                self.body_phase_start_time = now
                code = (
                    CODE_BODY_AUTO_TO_RIGHT
                    if self.current_side == "right"
                    else CODE_BODY_AUTO_TO_LEFT
                )
                return self._result(
                    code,
                    f"자동전환 / 15초 차례바꿈 ({self.current_side})",
                    sound_effect=body_sound,
                )

        elif self.state == "control_finish":
            go_back = inputs.has("backspace")
            go_to_game_select = inputs.has("space")
            if not go_back and not go_to_game_select:
                return StepResult()

            return_state = self.control_finish_return_state
            if return_state not in {"verbal_control", "nonverbal_control"}:
                raise RuntimeError(
                    f"control_finish 복귀 state가 올바르지 않습니다: {return_state}"
                )
            if go_back:
                if self.control_finish_enter_time is not None:
                    self.session_paused_duration += (
                        self.clock.getTime() - self.control_finish_enter_time
                    )
                self.state = return_state
                self.control_finish_return_state = None
                self.control_finish_enter_time = None
                code = (
                    CODE_VERBAL_CONTROL_RETURN
                    if return_state == "verbal_control"
                    else CODE_NONVERBAL_CONTROL_RETURN
                )
                return self._result(
                    code,
                    f"Backspace / control 종료화면 -> {return_state} 복귀",
                )

            code = (
                CODE_VERBAL_CONTROL_GAME_SELECT
                if return_state == "verbal_control"
                else CODE_NONVERBAL_CONTROL_GAME_SELECT
            )
            label = f"Space / control 종료화면({return_state}) -> 게임 고르기"
            self._reset_common_context()
            self.state = "select_game"
            self.clock.reset()
            return self._result(code, label)

        elif self.state == "exit_confirm":
            if inputs.has("left"):
                self.exit_cursor = (self.exit_cursor - 1) % 3
                return StepResult(clear_inputs=True)
            if inputs.has("right"):
                self.exit_cursor = (self.exit_cursor + 1) % 3
                return StepResult(clear_inputs=True)
            if not inputs.has("return"):
                return StepResult()

            if self.exit_cursor == 0:
                return self._result(
                    CODE_EXIT_YES,
                    "Enter / 게임 종료 확인: 예",
                    exit_after_flip=True,
                )
            if self.exit_cursor == 1:
                if self.exit_confirm_enter_time is not None:
                    paused = self.clock.getTime() - self.exit_confirm_enter_time
                    self._pause_active_timers(paused)
                    if self.previous_state_before_exit != "control_finish":
                        self.session_paused_duration += paused
                self.state = self.previous_state_before_exit or "select_game"
                self.previous_state_before_exit = None
                self.exit_confirm_enter_time = None
                return self._result(
                    CODE_EXIT_NO,
                    "Enter / 게임 종료 확인: 아니오",
                )

            self._reset_common_context()
            self.state = "select_game"
            self.previous_state_before_exit = None
            self.exit_confirm_enter_time = None
            self.clock.reset()
            return self._result(
                CODE_RESET_EXIT,
                "Enter / 종료 확인 -> 게임 고르기",
            )

        elif self.state == "try_answering":
            if inputs.has("left"):
                self.try_cursor = (self.try_cursor - 1) % 3
            elif inputs.has("right"):
                self.try_cursor = (self.try_cursor + 1) % 3

            if inputs.has("return") and self.try_cursor == 2:
                return_state = self.try_answering_return_state
                self._pause_answer_timer(return_state)
                self.try_answering_return_state = None
                self.state = return_state or "select_game"
                code = (
                    CODE_NAME_TRY_CANCEL
                    if return_state == "name_game"
                    else CODE_BODY_TRY_CANCEL
                )
                game_label = "name" if return_state == "name_game" else "body"
                return self._result(
                    code,
                    f"Enter / 정답시도 취소({game_label}) -> 차례유지",
                )

            decided: Optional[bool] = None
            if inputs.has("y"):
                decided = True
            elif inputs.has("n"):
                decided = False
            elif inputs.has("return"):
                decided = self.try_cursor == 0

            if decided is not None:
                return_state = self.try_answering_return_state
                self._pause_answer_timer(return_state)
                word_change = None
                if decided:
                    changed_side = opposite_side(self.current_side)
                    answered_word, following, _ = self.words.proceed(changed_side)
                    self.word_outcome_records[changed_side].append(
                        answered_word
                    )
                    word_change = self._word_change_label(changed_side, following)
                self.try_answering_return_state = None
                self.state = return_state or "select_game"
                if return_state == "name_game":
                    code = CODE_NAME_TRY_YES if decided else CODE_NAME_TRY_NO
                    game_label = "name"
                else:
                    code = CODE_BODY_TRY_YES if decided else CODE_BODY_TRY_NO
                    game_label = "body"
                answer_label = "정답맞음" if decided else "정답아님"
                label = f"{answer_label}({game_label}) -> 차례유지"
                if word_change is not None:
                    label = f"{label} | {word_change}"
                return self._result(code, label)

        return StepResult()

    @property
    def monitoring_state(self) -> Optional[str]:
        if self.state in ACTIVE_GAME_STATES:
            return self.state
        if self.state == "try_answering":
            return self.try_answering_return_state
        return None

    @property
    def verbal_control_sentence(self) -> str:
        return self.control.sentence

    @property
    def verbal_control_cursor(self) -> int:
        return self.control.confirm_cursor

    @property
    def verbal_control_sentence_index(self) -> int:
        return self.control.sentence_index
