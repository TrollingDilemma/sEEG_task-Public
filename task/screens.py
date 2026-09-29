from psychopy import visual

from .config import COLOR_SPACE, FONT_NAME, GRAY, SKY_BLUE, WHITE
from .state_utils import side_display
from .word_list_selector import grid_shape, row_indices


# PsychoPy 자극은 Window에 귀속되므로 (window id, callsite key)로 캐시한다.
_text_cache: dict = {}
_text_state: dict = {}
_rect_cache: dict = {}
_rect_state: dict = {}
_line_cache: dict = {}
_line_state: dict = {}
_outline_cache: dict = {}
_outline_state: dict = {}

UNSELECTED_LINE = [-0.2, -0.2, -0.2]   # 미선택 박스 테두리 (흐릿한 회색)
UNSELECTED_TEXT = [-0.15, -0.15, -0.15]  # 미선택 라벨 (흐릿)


def make_text(win, text: str, pos=(0, 0), height=32, color=WHITE, align="center", wrap_width=None, bold=False,):
    """프로젝트 공통 font를 사용하는 TextStim을 생성한다."""
    kwargs = dict(win=win, text=text, pos=pos, height=height, color=color, colorSpace=COLOR_SPACE, alignText=align, wrapWidth=wrap_width, bold=bold,)
    if FONT_NAME:
        kwargs["font"] = FONT_NAME
    return visual.TextStim(**kwargs)


def _safe_text_bounds(
    win,
    pos: tuple[float, float],
    wrap_width: float | None,
    max_width: float | None,
    max_height: float | None,
) -> tuple[float, float]:
    """현재 window와 text 중심점으로부터 화면 안쪽의 안전 bounds를 계산한다."""
    width = float(win.size[0])
    height = float(win.size[1])
    margin_x = max(4.0, width * 0.025)
    margin_y = max(4.0, height * 0.025)
    available_width = max(
        1.0,
        2.0 * (width / 2.0 - margin_x - abs(float(pos[0]))),
    )
    available_height = max(
        1.0,
        2.0 * (height / 2.0 - margin_y - abs(float(pos[1]))),
    )
    requested_width = available_width if wrap_width is None else float(wrap_width)
    if max_width is not None:
        requested_width = min(requested_width, float(max_width))
    if max_height is not None:
        available_height = min(available_height, float(max_height))
    return min(requested_width, available_width), available_height


def _fit_text_stim(stim, requested_height: float, max_width: float, max_height: float) -> None:
    """PsychoPy가 계산한 실제 bounding box가 bounds 안에 들도록 font를 축소한다."""
    stim.height = max(1.0, float(requested_height))
    stim.wrapWidth = max(1.0, float(max_width))
    for _ in range(4):
        try:
            bounds = stim.boundingBox
            rendered_width = float(bounds[0])
            rendered_height = float(bounds[1])
        except Exception:
            # Backend별 boundingBox 차이에 대비한 보수적 fallback.
            rendered_width = max_width
            line_count = max(1, str(stim.text).count("\n") + 1)
            rendered_height = float(stim.height) * line_count * 1.35
        scale = min(
            1.0,
            max_width / max(rendered_width, 1.0),
            max_height / max(rendered_height, 1.0),
        )
        if scale >= 0.995:
            break
        stim.height = max(1.0, float(stim.height) * scale * 0.97)


def _text(
    win,
    key,
    text,
    pos=(0, 0),
    height=32,
    color=WHITE,
    align="center",
    wrap_width=None,
    bold=False,
    max_width=None,
    max_height=None,
    auto_fit=True,
):
    """실제 window safe area 안으로 자동 축소되는 캐시 TextStim을 반환한다."""
    key = (id(win), key)
    safe_width, safe_height = _safe_text_bounds(
        win,
        tuple(pos),
        wrap_width,
        max_width,
        max_height,
    )
    layout_signature = (
        str(text),
        tuple(pos),
        float(height),
        float(safe_width),
        float(safe_height),
        align,
        bool(bold),
        bool(auto_fit),
        tuple(win.size),
    )
    stim = _text_cache.get(key)
    if stim is None:
        stim = make_text(
            win,
            text,
            pos=pos,
            height=height,
            color=color,
            align=align,
            wrap_width=safe_width,
            bold=bold,
        )
        _text_cache[key] = stim
        _text_state[key] = {
            "layout": None,
            "color": tuple(color),
        }
    st = _text_state[key]
    if st["layout"] != layout_signature:
        stim.text = text
        stim.pos = pos
        stim.alignText = align
        stim.bold = bold
        if auto_fit:
            _fit_text_stim(stim, height, safe_width, safe_height)
        else:
            stim.height = max(1.0, float(height))
            stim.wrapWidth = max(1.0, float(safe_width))
        st["layout"] = layout_signature
    if st["color"] != tuple(color):
        stim.color = color
        st["color"] = tuple(color)
    return stim


def _rect(win, key, width, height, pos, color):
    """캐시된 채움 Rect 반환. width/height/pos/color 가 바뀐 경우에만 갱신."""
    key = (id(win), key)
    r = _rect_cache.get(key)
    if r is None:
        r = visual.Rect(win=win, width=width, height=height, pos=pos, fillColor=color, lineColor=color, colorSpace=COLOR_SPACE,)
        _rect_cache[key] = r
        _rect_state[key] = {"w": width, "h": height, "pos": tuple(pos), "color": tuple(color)}
        return r
    st = _rect_state[key]
    if st["w"] != width:
        r.width = width
        st["w"] = width
    if st["h"] != height:
        r.height = height
        st["h"] = height
    if st["pos"] != tuple(pos):
        r.pos = pos
        st["pos"] = tuple(pos)
    if st["color"] != tuple(color):
        r.fillColor = color
        r.lineColor = color
        st["color"] = tuple(color)
    return r


def _outline(win, key, width, height, pos, line_color, line_width):
    """캐시된 테두리 Rect (내부는 배경색으로 채움). 선택 박스 시각화 전용."""
    key = (id(win), key)
    r = _outline_cache.get(key)
    if r is None:
        r = visual.Rect(win=win, width=width, height=height, pos=pos, fillColor=GRAY, lineColor=line_color, lineWidth=line_width, colorSpace=COLOR_SPACE,)
        _outline_cache[key] = r
        _outline_state[key] = {
            "w": width,
            "h": height,
            "pos": tuple(pos),
            "lc": tuple(line_color),
            "lw": line_width,
        }
        return r
    st = _outline_state[key]
    if st["w"] != width:
        r.width = width
        st["w"] = width
    if st["h"] != height:
        r.height = height
        st["h"] = height
    if st["pos"] != tuple(pos):
        r.pos = pos
        st["pos"] = tuple(pos)
    if st["lc"] != tuple(line_color):
        r.lineColor = line_color
        st["lc"] = tuple(line_color)
    if st["lw"] != line_width:
        r.lineWidth = line_width
        st["lw"] = line_width
    return r


def _line(win, key, start, end, line_color, line_width=2):
    """창 크기 변경 시 좌표까지 갱신되는 캐시 Line을 반환한다."""
    key = (id(win), key)
    ln = _line_cache.get(key)
    if ln is None:
        ln = visual.Line(win=win, start=start, end=end, lineColor=line_color, colorSpace=COLOR_SPACE, lineWidth=line_width,)
        _line_cache[key] = ln
        _line_state[key] = {
            "start": tuple(start),
            "end": tuple(end),
            "color": tuple(line_color),
            "width": line_width,
        }
        return ln
    state = _line_state[key]
    if state["start"] != tuple(start):
        ln.start = start
        state["start"] = tuple(start)
    if state["end"] != tuple(end):
        ln.end = end
        state["end"] = tuple(end)
    if state["color"] != tuple(line_color):
        ln.lineColor = line_color
        state["color"] = tuple(line_color)
    if state["width"] != line_width:
        ln.lineWidth = line_width
        state["width"] = line_width
    return ln


def draw_center_message(win, key: str, message: str, height=34) -> None:
    scaled_height = min(height, float(win.size[1]) * 0.04)
    stim = _text(
        win, key, message, pos=(0, 0), height=scaled_height,
        color=WHITE, align="center", wrap_width=float(win.size[0]) * 0.90,
    )
    stim.draw()


def side_to_korean(side: str) -> str:
    """participant side를 화면용 한글 label로 반환한다."""
    return side_display(side)


def draw_two_choice(win, key_prefix: str, title: str, left_label: str, right_label: str, cursor: int, hint: str) -> None:
    """좌우 방향키로 고르는 공통 2지선다 화면을 그린다."""
    w = win.size[0]
    h = win.size[1]
    box_w = w * 0.30
    box_h = h * 0.26
    left_x = -w * 0.22
    right_x = w * 0.22

    _text(win, key_prefix + "_title", title, pos=(0, h * 0.28), height=h * 0.045, color=WHITE, align="center", wrap_width=w * 0.9,).draw()

    for idx, (x, label) in enumerate([(left_x, left_label), (right_x, right_label)]):
        selected = (idx == cursor)
        line_c = SKY_BLUE if selected else UNSELECTED_LINE
        line_w = 3 if selected else 1
        txt_c = WHITE if selected else UNSELECTED_TEXT
        _outline(win, f"{key_prefix}_box{idx}", box_w, box_h, (x, 0), line_c, line_w).draw()
        _text(win, f"{key_prefix}_lbl{idx}", label, pos=(x, 0), height=h * 0.045, color=txt_c, align="center", wrap_width=box_w * 0.85, bold=selected,).draw()

    marker_x = (left_x if cursor == 0 else right_x) - box_w / 2 - w * 0.03
    _text(win, key_prefix + "_marker", "▶", pos=(marker_x, 0), height=h * 0.053, color=SKY_BLUE, align="center",).draw()

    _text(win, key_prefix + "_hint", hint, pos=(0, -h * 0.32), height=h * 0.029, color=WHITE, align="center", wrap_width=w * 0.9,).draw()


def draw_select_game_screen(win, cursor: int) -> None:
    width = float(win.size[0])
    height = float(win.size[1])
    labels = (
        "Verbal Control",
        "Nonverbal Control",
        "단어맞추기",
        "몸으로말해요",
    )
    gap = width * 0.025
    box_width = min(
        width * 0.205,
        (width * 0.90 - gap * (len(labels) - 1)) / len(labels),
    )
    box_height = height * 0.24
    total_width = len(labels) * box_width + (len(labels) - 1) * gap
    first_x = -total_width / 2 + box_width / 2

    _text(
        win,
        "sel_game_title",
        "어떤 게임을 할까요?",
        pos=(0, height * 0.29),
        height=height * 0.047,
        color=WHITE,
        wrap_width=width * 0.90,
    ).draw()
    for index, label in enumerate(labels):
        x = first_x + index * (box_width + gap)
        selected = index == cursor
        _outline(
            win,
            f"sel_game_box_{index}",
            box_width,
            box_height,
            (x, 0),
            SKY_BLUE if selected else UNSELECTED_LINE,
            3 if selected else 1,
        ).draw()
        _text(
            win,
            f"sel_game_label_{index}",
            label,
            pos=(x, 0),
            height=height * 0.038,
            color=WHITE if selected else UNSELECTED_TEXT,
            wrap_width=box_width * 0.86,
            max_width=box_width * 0.86,
            max_height=box_height * 0.75,
            bold=selected,
        ).draw()
    _text(
        win,
        "sel_game_hint",
        "← → 이동    Enter 확정    Ctrl+Q 종료",
        pos=(0, -height * 0.31),
        height=height * 0.029,
        color=WHITE,
        wrap_width=width * 0.90,
    ).draw()


def draw_verbal_control_confirm_screen(win, cursor: int) -> None:
    """Verbal Control 실행 여부를 좌우 방향키와 Enter로 확인한다."""
    draw_two_choice(
        win,
        "verbal_control_confirm",
        "Verbal Control을 진행할까요?",
        "예",
        "아니오",
        cursor,
        "← → 이동    Enter 확정    Ctrl+Q 종료",
    )


def draw_nonverbal_control_confirm_screen(win, cursor: int) -> None:
    """Nonverbal Control 실행 여부를 좌우 방향키와 Enter로 확인한다."""
    draw_two_choice(
        win,
        "nonverbal_control_confirm",
        "Nonverbal Control을 시작할까요?",
        "예",
        "아니오",
        cursor,
        "← → 이동    Enter 확정    Ctrl+Q 종료",
    )


def draw_control_finish_screen(win) -> None:
    """VC/NVC 완료 후 Space 또는 Backspace 입력을 안내한다."""
    draw_center_message(
        win,
        "control_finish",
        "Space: 게임고르기    Backspace: 이전화면으로",
        height=34 * 2,
    )


def draw_order_screen(win, body_game: bool, cursor: int) -> None:
    title = "몸으로말해요\n먼저 시작할 사람은?" if body_game else "단어맞추기\n먼저 시작할 사람은?"
    draw_two_choice(win, "order", title, side_display("left"), side_display("right"), cursor,
                    "← → 이동    Enter 확정    R 게임 다시 고르기",)

def draw_name_start_confirm_screen(win, first_side: str) -> None:
    message = (
        f"먼저 시작할 사람: {side_to_korean(first_side)}\n\n"
        "Enter: 게임 시작    R: 순서 재설정"
    )
    draw_center_message(win, "name_start_confirm", message, height=34 * 2)

def draw_body_start_confirm_screen(win, first_side: str) -> None:
    message = (
        f"먼저 시작할 사람: {side_to_korean(first_side)}\n\n"
        "Enter: 게임 시작    R: 순서 재설정"
        )
    draw_center_message(win, "body_start_confirm", message, height=34 * 2)

def draw_exit_confirm_screen(win, cursor: int) -> None:
    """Ctrl+Q 이후 세 선택지를 가로 상자로 표시한다."""
    width = float(win.size[0])
    height = float(win.size[1])
    labels = ("예", "아니오", "게임 고르기")
    box_width = width * 0.23
    box_height = height * 0.23
    gap = width * 0.035
    total_width = len(labels) * box_width + (len(labels) - 1) * gap
    first_x = -total_width / 2 + box_width / 2

    _text(
        win,
        "exit_confirm_title",
        "프로그램을 완전 종료할까요?",
        pos=(0, height * 0.27),
        height=height * 0.050,
        color=WHITE,
        wrap_width=width * 0.90,
    ).draw()
    for index, label in enumerate(labels):
        x = first_x + index * (box_width + gap)
        selected = index == cursor
        _outline(
            win,
            f"exit_confirm_box_{index}",
            box_width,
            box_height,
            (x, 0),
            SKY_BLUE if selected else UNSELECTED_LINE,
            3 if selected else 1,
        ).draw()
        _text(
            win,
            f"exit_confirm_label_{index}",
            label,
            pos=(x, 0),
            height=height * 0.043,
            color=WHITE if selected else UNSELECTED_TEXT,
            wrap_width=box_width * 0.85,
            bold=selected,
        ).draw()
    _text(
        win,
        "exit_confirm_hint",
        "← → 이동    Enter 확정",
        pos=(0, -height * 0.31),
        height=height * 0.029,
        color=WHITE,
        wrap_width=width * 0.90,
    ).draw()


def draw_word_list_select_screen(
    win,
    *,
    game_label: str,
    available_names: list[str],
    cursor: int,
) -> None:
    """Display 0에 방향키로 선택하는 최대 4열 word-list grid를 그린다."""
    width = float(win.size[0])
    height = float(win.size[1])
    rows, columns = grid_shape(len(available_names))
    horizontal_gap = width * 0.025
    vertical_gap = height * 0.035
    grid_width = width * 0.90
    grid_height = height * 0.50
    box_width = min(
        width * 0.30,
        (grid_width - horizontal_gap * (columns - 1)) / columns,
    )
    box_height = min(
        height * 0.17,
        (grid_height - vertical_gap * (rows - 1)) / rows,
    )
    total_grid_height = rows * box_height + (rows - 1) * vertical_gap
    top_y = height * 0.13 + total_grid_height / 2 - box_height / 2

    _rect(win, "word_list_background", width, height, (0, 0), GRAY).draw()
    _text(
        win,
        "word_list_title",
        f"{game_label}\n사용할 word list를 선택하세요",
        pos=(0, height * 0.37),
        height=height * 0.045,
        color=WHITE,
        wrap_width=width * 0.85,
    ).draw()

    for row in range(rows):
        indices = list(row_indices(row, len(available_names)))
        row_width = len(indices) * box_width + (len(indices) - 1) * horizontal_gap
        first_x = -row_width / 2 + box_width / 2
        y = top_y - row * (box_height + vertical_gap)
        for column, index in enumerate(indices):
            x = first_x + column * (box_width + horizontal_gap)
            selected = index == cursor
            _outline(
                win,
                f"word_list_option_{index}",
                box_width,
                box_height,
                (x, y),
                SKY_BLUE if selected else UNSELECTED_LINE,
                3 if selected else 1,
            ).draw()
            _text(
                win,
                f"word_list_option_text_{index}",
                f"word_list_{available_names[index]}.txt",
                pos=(x, y),
                height=min(height * 0.030, box_height * 0.28),
                color=WHITE if selected else UNSELECTED_TEXT,
                wrap_width=box_width * 0.90,
                bold=selected,
            ).draw()

    _text(
        win,
        "word_list_hint",
        "← → 이동    Enter 확정    R 순서 재설정",
        pos=(0, -height * 0.43),
        height=height * 0.025,
        color=WHITE,
        wrap_width=width * 0.90,
    ).draw()
