"""임의 길이 word-list의 로딩과 순환을 검증한다."""

from pathlib import Path
from tempfile import TemporaryDirectory

from psychopy import core

import task.words as words_module
from task.game_state import GameState
from task.models import InputFrame
from task.word_state import WordState


def _write_list(directory: Path, name: str, words: list[str]) -> None:
    path = directory / f"word_list_{name}.txt"
    path.write_text("\n".join(words), encoding="utf-8")


def main() -> None:
    original_directory = words_module.WORD_LISTS_DIR
    try:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            words_module.WORD_LISTS_DIR = directory

            for count in (1, 3, 31):
                name = f"count_{count}"
                expected = [f"단어_{index}" for index in range(count)]
                _write_list(directory, name, expected)
                assert words_module.load_word_list(name) == expected

                state = WordState(list_name=name)
                assert set(state.arrays["left"]) == set(expected)
                assert set(state.arrays["right"]) == set(expected)
                if count > 1:
                    assert state.current("left") != state.current("right")

            # 한 칸 앞이 상대 행의 현재 단어이면 중간 위치를 표시하지 않고
            # 원자적으로 두 칸 진행한다. 이 규칙은 양쪽에 대칭이다.
            state = WordState(list_name="count_3")
            state.arrays = {
                "left": ["단어_0", "단어_1", "단어_2"],
                "right": ["단어_1", "단어_2", "단어_0"],
            }
            state.indices = {"left": 0, "right": 0}
            previous, following, next_index = state.proceed("left")
            assert (previous, following, next_index) == ("단어_0", "단어_2", 2)
            assert state.current("left") != state.current("right")

            state.indices = {"left": 0, "right": 1}
            previous, following, next_index = state.proceed("right")
            assert (previous, following, next_index) == ("단어_2", "단어_1", 0)
            assert state.current("left") != state.current("right")

            # 단일 단어 목록은 기존처럼 index 0으로 순환한다.
            singleton = WordState(list_name="count_1")
            first = singleton.current("left")
            _, following, next_index = singleton.proceed("left")
            assert next_index == 0
            assert following == first

            _write_list(directory, "empty", [])
            try:
                words_module.load_word_list("empty")
            except ValueError as exc:
                assert "at least one" in str(exc)
            else:
                raise AssertionError("빈 word-list는 거부해야 합니다.")

            _write_list(directory, "duplicate", ["사과", "사과"])
            try:
                words_module.load_word_list("duplicate")
            except ValueError as exc:
                assert "Duplicate" in str(exc)
            else:
                raise AssertionError("중복 word는 거부해야 합니다.")
    finally:
        words_module.WORD_LISTS_DIR = original_directory

    game = GameState(core.Clock(), 15.0)
    assert game.word_list_cursor == 0
    for order_state, expected_list_state in (
        ("name_order", "name_word_list"),
        ("body_order", "body_word_list"),
    ):
        game.state = order_state
        game.word_list_cursor = len(game.available_word_lists) - 1
        game.step(InputFrame(frozenset({"return"})))
        assert game.state == expected_list_state
        assert game.word_list_cursor == 0

    print("Word-list test passed.")


if __name__ == "__main__":
    main()
