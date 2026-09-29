"""Cursor macro의 비-Win32 fallback 중앙 좌표 계산을 검증한다."""

from task.cursor_macro import move_cursor_to_window_center
from task.input_router import CURSOR_MACRO_KEYS, apply_game_key_bindings


class _FakeHandle:
    def __init__(self):
        self.position = None

    @staticmethod
    def get_size():
        return 901, 501

    def set_mouse_position(self, x, y):
        self.position = (x, y)


class _FakeWindow:
    def __init__(self):
        self.winHandle = _FakeHandle()


def main() -> None:
    window = _FakeWindow()
    move_cursor_to_window_center(window)
    assert window.winHandle.position == (450, 250)
    assert CURSOR_MACRO_KEYS == {"0"}

    name_keys = {"minus", "equal"}
    apply_game_key_bindings(name_keys, "name_game")
    assert {"space", "return"}.issubset(name_keys)

    body_keys = {"minus", "equal"}
    apply_game_key_bindings(body_keys, "body_game")
    assert "return" in body_keys
    assert "space" not in body_keys

    inactive_keys = {"minus", "equal"}
    apply_game_key_bindings(inactive_keys, "select_game")
    assert inactive_keys == {"minus", "equal"}
    print("Cursor macro test passed.")


if __name__ == "__main__":
    main()
