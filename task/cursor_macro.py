"""Windows cursor를 Display 0 client 영역 중앙으로 이동한다."""

import ctypes

from pyglet.libs.win32 import _user32
from pyglet.libs.win32.types import POINT, RECT


VK_TOP_ROW_0 = 0x30


class TopRowZeroEdgeDetector:
    """PsychoPy와 무관하게 Windows 상단 숫자열 0의 key-down edge를 감지한다."""

    def __init__(self):
        self._was_down = False

    def poll(self) -> bool:
        user32 = ctypes.windll.user32
        is_down = bool(user32.GetAsyncKeyState(VK_TOP_ROW_0) & 0x8000)
        pressed = is_down and not self._was_down
        self._was_down = is_down
        return pressed


def move_cursor_to_window_center(window) -> bool:
    """PsychoPy pyglet Window의 client 중앙을 Windows 절대 좌표로 변환한다."""
    handle = window.winHandle
    hwnd = getattr(handle, "_view_hwnd", None) or getattr(handle, "_hwnd", None)
    if hwnd is None:
        width, height = handle.get_size()
        handle.set_mouse_position(int(width) // 2, int(height) // 2)
        return True

    client_rect = RECT()
    if not _user32.GetClientRect(hwnd, ctypes.byref(client_rect)):
        raise ctypes.WinError()
    center = POINT(
        (client_rect.right - client_rect.left) // 2,
        (client_rect.bottom - client_rect.top) // 2,
    )
    if not _user32.ClientToScreen(hwnd, ctypes.byref(center)):
        raise ctypes.WinError()
    # 다른 PsychoPy/pyglet Window가 cursor clipping을 설정했어도 먼저 해제한다.
    _user32.ClipCursor(None)
    if not _user32.SetCursorPos(center.x, center.y):
        raise ctypes.WinError()
    actual = POINT()
    if not _user32.GetCursorPos(ctypes.byref(actual)):
        raise ctypes.WinError()
    if (actual.x, actual.y) != (center.x, center.y):
        # 일부 driver가 첫 warp를 무시하는 경우 한 번 더 요청한다.
        _user32.SetCursorPos(center.x, center.y)
        if not _user32.GetCursorPos(ctypes.byref(actual)):
            raise ctypes.WinError()
    return (actual.x, actual.y) == (center.x, center.y)
