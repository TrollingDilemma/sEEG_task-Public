"""GameState를 Display 0/1/2 화면으로 routing하고 flip/TTL을 동기화한다."""

from .config import PHOTODIODE_FLASH_FRAMES
from .game_state import (
    HOST_MANIPULATION_STATES,
    GameState,
    TriggerEvent,
)
from .operator_screens import (
    draw_nonverbal_control_operator_screen,
    draw_operator_monitoring_screen,
    draw_photodiode_marker,
    draw_verbal_control_operator_screen,
)
from .screens import (
    draw_body_start_confirm_screen,
    draw_control_finish_screen,
    draw_exit_confirm_screen,
    draw_name_start_confirm_screen,
    draw_nonverbal_control_confirm_screen,
    draw_order_screen,
    draw_select_game_screen,
    draw_verbal_control_confirm_screen,
    draw_word_list_select_screen,
)
from .state_utils import get_side_name
from .wisecoco_screens import (
    draw_nonverbal_control_instruction_screen,
    draw_wisecoco_answer_attempt_indicator,
    draw_wisecoco_game_screen,
    draw_wisecoco_host_adjusting_screen,
    draw_verbal_control_sentence_screen,
)


class DisplayRouter:
    def __init__(self, display_windows, trigger_sync, *, touch_enabled: bool = True):
        self.windows = display_windows
        self.trigger_sync = trigger_sync
        self.touch_enabled = touch_enabled
        self._photodiode_frames_remaining = 0

    def render(self, game: GameState) -> None:
        draw_now = game.clock.getTime()
        answer_elapsed = (
            draw_now - game.try_answering_enter_time
            if game.state == "try_answering"
            and game.try_answering_enter_time is not None
            else 0.0
        )
        for display_index, target_win in enumerate(self.windows.all):
            monitoring_state = game.monitoring_state
            if display_index == 0 and game.state == "verbal_control":
                draw_verbal_control_operator_screen(
                    target_win,
                    session_elapsed=max(
                        0.0,
                        draw_now - game.session_paused_duration,
                    ),
                    sentence=game.verbal_control_sentence,
                    sentence_index=game.verbal_control_sentence_index,
                )
                continue

            if display_index == 0 and game.state == "nonverbal_control":
                draw_nonverbal_control_operator_screen(
                    target_win,
                    session_elapsed=max(
                        0.0,
                        draw_now - game.session_paused_duration,
                    ),
                )
                continue

            if display_index == 1 and game.state == "verbal_control":
                draw_verbal_control_sentence_screen(
                    target_win,
                    game.verbal_control_sentence,
                )
                continue

            if display_index == 1 and game.state == "nonverbal_control":
                draw_nonverbal_control_instruction_screen(target_win)
                continue

            if display_index == 2 and game.state == "verbal_control":
                draw_wisecoco_host_adjusting_screen(target_win)
                continue

            if display_index == 2 and game.state == "nonverbal_control":
                draw_nonverbal_control_instruction_screen(target_win)
                continue

            if display_index == 0 and monitoring_state in {"name_game", "body_game"}:
                monitoring_game = (
                    "verbal" if monitoring_state == "name_game" else "nonverbal"
                )
                if monitoring_game == "nonverbal":
                    reference_time = (
                        game.try_answering_enter_time
                        if game.state == "try_answering"
                        and game.try_answering_enter_time is not None
                        else draw_now
                    )
                    phase_progress = (
                        reference_time - game.body_phase_start_time
                    ) / game.body_duration
                else:
                    phase_progress = 0.0
                draw_operator_monitoring_screen(
                    target_win,
                    game=monitoring_game,
                    current_side=game.current_side,
                    left_name=get_side_name("left"),
                    right_name=get_side_name("right"),
                    left_current_word=game.words.current("left"),
                    right_current_word=game.words.current("right"),
                    left_word_outcomes=game.word_outcome_records["left"],
                    right_word_outcomes=game.word_outcome_records["right"],
                    session_elapsed=max(
                        0.0,
                        draw_now - game.session_paused_duration,
                    ),
                    phase_progress=phase_progress,
                    answer_attempting=game.state == "try_answering",
                    answer_attempt_elapsed=answer_elapsed,
                    answer_cursor=game.try_cursor,
                )
                continue

            if display_index > 0 and game.state in HOST_MANIPULATION_STATES:
                draw_wisecoco_host_adjusting_screen(target_win)
                continue

            activated_side = "left" if display_index == 1 else "right"
            if display_index > 0 and monitoring_state == "name_game":
                draw_wisecoco_game_screen(
                    target_win,
                    game="verbal",
                    activation=activated_side == game.current_side,
                    word=game.words.current(activated_side),
                    touch_enabled=self.touch_enabled,
                )
                if game.state == "try_answering":
                    draw_wisecoco_answer_attempt_indicator(
                        target_win,
                        answer_elapsed,
                        activation=activated_side == game.current_side,
                    )
                continue
            if display_index > 0 and monitoring_state == "body_game":
                reference_time = (
                    game.try_answering_enter_time
                    if game.state == "try_answering"
                    and game.try_answering_enter_time is not None
                    else draw_now
                )
                draw_wisecoco_game_screen(
                    target_win,
                    game="nonverbal",
                    activation=activated_side == game.current_side,
                    word=game.words.current(activated_side),
                    phase_progress=(
                        reference_time - game.body_phase_start_time
                    ) / game.body_duration,
                    touch_enabled=self.touch_enabled,
                )
                if game.state == "try_answering":
                    draw_wisecoco_answer_attempt_indicator(
                        target_win,
                        answer_elapsed,
                        activation=activated_side == game.current_side,
                    )
                continue

            if game.state == "select_game":
                draw_select_game_screen(target_win, game.select_cursor)
            elif game.state == "verbal_control_confirm":
                draw_verbal_control_confirm_screen(
                    target_win,
                    game.verbal_control_cursor,
                )
            elif game.state == "nonverbal_control_confirm":
                draw_nonverbal_control_confirm_screen(
                    target_win,
                    game.verbal_control_cursor,
                )
            elif game.state == "name_order":
                draw_order_screen(target_win, body_game=False, cursor=game.order_cursor)
            elif game.state == "name_start_confirm":
                draw_name_start_confirm_screen(target_win, game.first_side)
            elif game.state == "name_word_list":
                draw_word_list_select_screen(
                    target_win,
                    game_label="단어맞추기",
                    available_names=game.available_word_lists,
                    cursor=game.word_list_cursor,
                )
            elif game.state == "body_order":
                draw_order_screen(target_win, body_game=True, cursor=game.order_cursor)
            elif game.state == "body_start_confirm":
                draw_body_start_confirm_screen(target_win, game.first_side)
            elif game.state == "body_word_list":
                draw_word_list_select_screen(
                    target_win,
                    game_label="몸으로말해요",
                    available_names=game.available_word_lists,
                    cursor=game.word_list_cursor,
                )
            elif game.state == "control_finish":
                draw_control_finish_screen(target_win)
            elif game.state == "exit_confirm":
                draw_exit_confirm_screen(target_win, game.exit_cursor)

    def present(self, trigger: TriggerEvent | None) -> None:
        if trigger is not None:
            self._photodiode_frames_remaining = PHOTODIODE_FLASH_FRAMES
        if self._photodiode_frames_remaining > 0:
            # 모든 Display 0 UI 위에 마지막으로 그려 photodiode patch를 보장한다.
            draw_photodiode_marker(self.windows.operator)
            self._photodiode_frames_remaining -= 1
        if trigger is not None:
            self.trigger_sync.prepare(
                # TTL edge와 photodiode marker onset은 같은 Display 0 flip에 묶는다.
                self.windows.operator,
                trigger.code,
                trigger.label,
                sound_effect=trigger.sound_effect,
            )
        self.windows.flip_all()
        if trigger is not None:
            self.trigger_sync.finish()
