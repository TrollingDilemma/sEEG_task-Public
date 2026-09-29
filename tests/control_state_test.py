"""Control state, 전용 종료화면 및 TTL code 전이를 검증한다."""

from psychopy import core

from task.control_state import ControlState
from task.game_state import GameState
from task.models import InputFrame


def _input(*keys: str) -> InputFrame:
    return InputFrame(frozenset(keys))


def main() -> None:
    control = ControlState()
    assert control.confirm_cursor == 1

    control.step("verbal_control_confirm", _input("left"))
    result = control.step("verbal_control_confirm", _input("return"))
    assert result is not None
    assert result.code == 50
    assert result.next_state == "verbal_control"
    assert result.label.endswith("i=1")

    result = control.step("verbal_control", _input("space"))
    assert result is not None
    assert result.code == 52
    assert control.sentence_index == 1
    assert result.label.endswith("i=2")

    result = control.step("verbal_control", _input("backspace"))
    assert result is not None
    assert result.code == 53
    assert control.sentence_index == 0
    assert result.label.endswith("i=1")

    control.sentence_index = 9
    result = control.step("verbal_control", _input("space"))
    assert result is not None
    assert result.code == 54
    assert result.next_state == "control_finish"
    assert result.label.endswith("i=10")

    result = control.step("nonverbal_control", _input("space"))
    assert result is not None
    assert result.code == 63
    assert result.next_state == "control_finish"

    transition_sound = object()
    game = GameState(
        core.Clock(),
        15.0,
        state_transition_sound=transition_sound,
    )
    game.select_cursor = 0
    assert game.step(_input("return")).trigger.code == 40
    assert game.verbal_control_cursor == 1
    game.step(_input("left"))
    result = game.step(_input("return"))
    assert result.trigger.code == 50
    assert result.trigger.sound_effect is transition_sound
    game.control.sentence_index = 9
    assert game.step(_input("space")).trigger.code == 54
    assert game.state == "control_finish"
    assert game.control_finish_return_state == "verbal_control"
    assert game.step(_input("backspace")).trigger.code == 55
    assert game.state == "verbal_control"

    assert game.step(_input("space")).trigger.code == 54
    assert game.step(_input("space")).trigger.code == 56
    assert game.state == "select_game"

    game.select_cursor = 1
    result = game.step(_input("return"))
    assert result.trigger.code == 60
    assert result.trigger.sound_effect is None
    assert game.state == "nonverbal_control_confirm"
    game.step(_input("right"))
    assert game.step(_input("return")).trigger.code == 62
    assert game.state == "select_game"

    game.select_cursor = 1
    result = game.step(_input("return"))
    assert result.trigger.code == 60
    assert result.trigger.sound_effect is None
    assert game.verbal_control_cursor == 1
    result = game.step(_input("return"))
    assert result.trigger.code == 62
    assert game.state == "select_game"

    game.select_cursor = 1
    game.step(_input("return"))
    game.step(_input("left"))
    result = game.step(_input("return"))
    assert result.trigger.code == 61
    assert result.trigger.sound_effect is transition_sound
    assert game.state == "nonverbal_control"
    assert game.step(_input("space")).trigger.code == 63
    assert game.state == "control_finish"
    assert game.control_finish_return_state == "nonverbal_control"
    assert game.step(_input("backspace")).trigger.code == 64
    assert game.state == "nonverbal_control"

    assert game.step(_input("space")).trigger.code == 63
    assert game.step(_input("space")).trigger.code == 65
    assert game.state == "select_game"

    for start_state, expected_code in (
        ("name_start_confirm", 12),
        ("body_start_confirm", 22),
    ):
        start_game = GameState(
            core.Clock(),
            15.0,
            state_transition_sound=transition_sound,
        )
        start_game.state = start_state
        start_game.first_side = "left"
        result = start_game.step(_input("return"))
        assert result.trigger.code == expected_code
        assert result.trigger.sound_effect is transition_sound

    assert GameState._word_change_label("left", "우산") == "왼쪽 단어: 우산"
    assert "->" not in GameState._word_change_label("right", "냉장고")

    outcomes = GameState(core.Clock(), 15.0)
    outcomes.state = "name_start_confirm"
    outcomes.first_side = "left"
    outcomes.step(_input("return"))
    passed_word = outcomes.words.current("left")
    outcomes.step(_input("p"))
    assert outcomes.word_outcome_records["left"] == [f"{passed_word}(PASS)"]

    answered_word = outcomes.words.current("right")
    outcomes.step(_input("return"))
    assert outcomes.try_cursor == 1
    outcomes.step(_input("left"))
    outcomes.step(_input("return"))
    assert outcomes.word_outcome_records["left"] == [f"{passed_word}(PASS)"]
    assert outcomes.word_outcome_records["right"] == [answered_word]

    print("ControlState test passed.")


if __name__ == "__main__":
    main()
