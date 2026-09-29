"""Display 0(laptop)에 표시되는 host용 in-game monitoring 화면."""

from .config import (
    ANSWER_INDICATOR_BLINK_HZ,
    BLACK,
    GRAY,
    GREEN,
    ORANGE,
    RED,
    SKY_BLUE,
    WHITE,
)
from .screens import _line, _outline, _rect, _text


INDICATOR_SIDE_RATIO = 0.090
NONVERBAL_INDICATOR_HEIGHT_RATIO = 0.5
WORD_OUTCOME_ROWS_PER_COLUMN = 25
WORD_OUTCOME_COLUMN_WIDTH_RATIO = 0.75


def _side_label(side: str, name: str) -> str:
    direction = "Lt" if side == "left" else "Rt"
    return f"{direction}({name})" if name else direction


def draw_photodiode_marker(win) -> None:
    """Display 0 최좌하단에 indicator와 같은 크기의 pure-white square를 그린다."""
    width = float(win.size[0])
    height = float(win.size[1])
    size = min(width, height) * INDICATOR_SIDE_RATIO
    position = (-width / 2 + size / 2, -height / 2 + size / 2)
    _rect(
        win,
        "operator_photodiode_marker",
        size,
        size,
        position,
        WHITE,
    ).draw()


def _draw_activation_indicator(
    win,
    *,
    side: str,
    active: bool,
    game: str,
    phase_progress: float,
    center_x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    key = f"operator_activation_{side}"
    _outline(win, key + "_outline", width, height, (center_x, y), GREEN, 2).draw()
    if active:
        fill_ratio = 1.0 if game == "verbal" else 1.0 - max(0.0, min(1.0, phase_progress))
        inner_width = max(0.0, width - 4)
        inner_height = max(0.0, height - 4)
        fill_height = inner_height * fill_ratio
        if fill_height > 0:
            fill_y = y - inner_height / 2 + fill_height / 2
            _rect(
                win, key + "_fill", inner_width, fill_height,
                (center_x, fill_y), GREEN,
            ).draw()


def _draw_answer_indicator(
    win,
    *,
    side: str,
    attempting: bool,
    blink_filled: bool,
    center_x: float,
    y: float,
    size: float,
) -> None:
    key = f"operator_answer_{side}"
    if attempting and blink_filled:
        _rect(win, key + "_fill", size, size, (center_x, y), RED).draw()
    else:
        _outline(win, key + "_outline", size, size, (center_x, y), RED, 2).draw()


def _draw_answer_popup(
    win,
    *,
    side: str,
    name: str,
    cursor: int,
    side_center_x: float,
    half_width: float,
    height: float,
) -> None:
    popup_w = half_width * 0.78
    popup_h = height * 0.38
    popup_y = -height * 0.08
    _outline(
        win, f"operator_popup_{side}", popup_w, popup_h,
        (side_center_x, popup_y), SKY_BLUE, 2.5,
    ).draw()
    label = _side_label(side, name)
    _text(
        win, f"operator_popup_title_{side}", f"{label}가 정답을 맞추었나요?",
        pos=(side_center_x, popup_y + popup_h * 0.31), height=height * 0.032,
        color=WHITE, wrap_width=popup_w * 0.9,
    ).draw()

    option_y = popup_y
    for index, (text, offset, width) in enumerate(
        (("예", -0.32, 0.16), ("아니오", -0.08, 0.22), ("정답시도취소", 0.26, 0.40))
    ):
        x = side_center_x + popup_w * offset
        selected = index == cursor
        _outline(
            win, f"operator_popup_option_{side}_{index}",
            popup_w * width, popup_h * 0.20, (x, option_y),
            SKY_BLUE if selected else WHITE, 2 if selected else 1,
        ).draw()
        _text(
            win, f"operator_popup_option_text_{side}_{index}", text,
            pos=(x, option_y), height=height * 0.030, color=WHITE,
        ).draw()

    _text(
        win, f"operator_popup_hint_{side}",
        "← → 이동    Enter 선택",
        pos=(side_center_x, popup_y - popup_h * 0.34),
        height=height * 0.020, color=WHITE, wrap_width=popup_w * 0.9,
    ).draw()


def draw_operator_monitoring_screen(
    win,
    *,
    game: str,
    current_side: str,
    left_name: str,
    right_name: str,
    left_current_word: str,
    right_current_word: str,
    left_word_outcomes: list[str],
    right_word_outcomes: list[str],
    session_elapsed: float,
    phase_progress: float = 0.0,
    answer_attempting: bool = False,
    answer_attempt_elapsed: float = 0.0,
    answer_cursor: int = 0,
) -> None:
    """LT/RT 상태를 한 화면에서 감시하는 Display 0 전용 화면."""
    width = float(win.size[0])
    height = float(win.size[1])
    half_width = width / 2
    side_centers = {"left": -width / 4, "right": width / 4}
    names = {"left": left_name, "right": right_name}
    current_words = {"left": left_current_word, "right": right_current_word}
    word_outcomes = {"left": left_word_outcomes, "right": right_word_outcomes}

    _rect(win, "operator_background", width, height, (0, 0), GRAY).draw()
    _line(
        win, "operator_center_line", (0, -height / 2), (0, height / 2),
        SKY_BLUE, 2,
    ).draw()

    for side in ("left", "right"):
        center_x = side_centers[side]
        label_x = (
            center_x - half_width * 0.28
            if side == "left"
            else center_x + half_width * 0.28
        )
        label_width = half_width * 0.32
        _text(
            win, f"operator_name_{side}", _side_label(side, names[side]),
            pos=(label_x, height * 0.42), height=height * 0.035,
            color=WHITE, align="center", wrap_width=label_width,
            max_width=label_width, max_height=height * 0.075,
        ).draw()
        record_text_height = height * 0.035 * 0.7 * (5 / 7)
        record_spacing = record_text_height * 0.5
        record_column_width = label_width * WORD_OUTCOME_COLUMN_WIDTH_RATIO
        outer_margin = record_spacing
        first_column_x = (
            -width / 2 + outer_margin + record_column_width / 2
            if side == "left"
            else width / 2 - outer_margin - record_column_width / 2
        )
        for record_index, record_text in enumerate(word_outcomes[side]):
            column_index, row_index = divmod(
                record_index,
                WORD_OUTCOME_ROWS_PER_COLUMN,
            )
            column_direction = 1 if side == "left" else -1
            record_x = (
                first_column_x
                + column_direction
                * column_index
                * (record_column_width + record_spacing)
            )
            _text(
                win,
                f"operator_word_outcome_{side}_{record_index}",
                record_text,
                pos=(
                    record_x,
                    height * 0.34
                    - row_index * (record_text_height + record_spacing),
                ),
                height=record_text_height,
                color=WHITE,
                align="center",
                wrap_width=record_column_width,
                max_width=record_column_width,
                auto_fit=False,
            ).draw()
        _rect(
            win, f"operator_pass_bg_{side}", half_width * 0.20, height * 0.075,
            (center_x, height * 0.41), ORANGE,
        ).draw()
        _text(
            win, f"operator_pass_text_{side}", "PASS: P",
            pos=(center_x, height * 0.41), height=height * 0.032,
            color=WHITE, bold=True,
            max_width=half_width * 0.18, max_height=height * 0.065,
        ).draw()

        _text(
            win, f"operator_current_word_{side}", current_words[side],
            pos=(center_x, height * 0.08), height=height * 0.052,
            color=WHITE, wrap_width=half_width * 0.82, bold=True,
            max_width=half_width * 0.82, max_height=height * 0.24,
        ).draw()
        indicator_x = center_x + (half_width * 0.30 if side == "left" else -half_width * 0.30)
        indicator_size = min(width, height) * INDICATOR_SIDE_RATIO
        activation_height = (
            height * NONVERBAL_INDICATOR_HEIGHT_RATIO
            if game == "nonverbal"
            else indicator_size
        )
        activation_y = height * (0.21 if game == "nonverbal" else 0.41)
        active = side == current_side
        _draw_activation_indicator(
            win, side=side, active=active, game=game,
            phase_progress=phase_progress, center_x=indicator_x,
            y=activation_y, width=indicator_size, height=activation_height,
        )
        answer_x = indicator_x
        answer_y = height * 0.31
        if game == "nonverbal":
            # 초록 indicator의 안쪽 경계와 중앙 하늘색 구분선 사이 정중앙.
            inner_gap_width = max(0.0, abs(indicator_x) - indicator_size / 2)
            answer_x = (-1 if side == "left" else 1) * inner_gap_width / 2
            answer_y = activation_y
        _draw_answer_indicator(
            win, side=side,
            attempting=(answer_attempting and active),
            blink_filled=(
                int(answer_attempt_elapsed * ANSWER_INDICATOR_BLINK_HZ * 2)
                % 2
                == 0
            ),
            center_x=answer_x, y=answer_y, size=indicator_size,
        )

    minutes = int(session_elapsed // 60)
    seconds = session_elapsed - minutes * 60
    _text(
        win, "operator_elapsed",
        f"Total elapsed time: {minutes:02d}min {seconds:06.3f}sec",
        # TextStim의 wrap 영역 전체가 화면 우측 절반 안에 있도록 배치한다.
        pos=(width * 0.245, -height * 0.43), height=height * 0.026,
        color=BLACK, align="right", wrap_width=width * 0.46,
        max_width=width * 0.46, max_height=height * 0.075,
    ).draw()

    if answer_attempting:
        _draw_answer_popup(
            win, side=current_side, name=names[current_side], cursor=answer_cursor,
            side_center_x=side_centers[current_side], half_width=half_width,
            height=height,
        )


def draw_verbal_control_operator_screen(
    win,
    session_elapsed: float,
    sentence: str,
    sentence_index: int,
) -> None:
    """Display 0에 현재 Verbal Control 문장·index와 timer를 표시한다."""
    width = float(win.size[0])
    height = float(win.size[1])
    _rect(win, "vc_operator_background", width, height, (0, 0), GRAY).draw()
    _text(
        win,
        "vc_operator_hint",
        "space: 문장 넘기기    backspace: 문장 되돌리기",
        pos=(0, height * 0.07),
        height=height * 0.040,
        color=WHITE,
        wrap_width=width * 0.90,
        max_width=width * 0.90,
        max_height=height * 0.20,
    ).draw()
    _text(
        win,
        "vc_operator_sentence",
        f'"{sentence}" | i={sentence_index + 1}',
        pos=(0, -height * 0.02),
        height=height * 0.040 * 0.7,
        color=WHITE,
        wrap_width=width * 0.90,
        max_width=width * 0.90,
        max_height=height * 0.20,
    ).draw()
    minutes = int(session_elapsed // 60)
    seconds = session_elapsed - minutes * 60
    _text(
        win,
        "vc_operator_elapsed",
        f"Total elapsed time: {minutes:02d}min {seconds:06.3f}sec",
        pos=(width * 0.245, -height * 0.43),
        height=height * 0.026,
        color=BLACK,
        align="right",
        wrap_width=width * 0.46,
        max_width=width * 0.46,
        max_height=height * 0.075,
    ).draw()


def draw_nonverbal_control_operator_screen(win, session_elapsed: float) -> None:
    """Display 0 Nonverbal Control 안내와 session timer를 표시한다."""
    width = float(win.size[0])
    height = float(win.size[1])
    _rect(win, "nvc_operator_background", width, height, (0, 0), GRAY).draw()
    _text(
        win,
        "nvc_operator_hint",
        "동작을 수행하도록 안내하세요\n\nSpace: Nonverbal Control 종료",
        pos=(0, 0),
        height=height * 0.040,
        color=WHITE,
        wrap_width=width * 0.90,
        max_width=width * 0.90,
        max_height=height * 0.30,
    ).draw()
    minutes = int(session_elapsed // 60)
    seconds = session_elapsed - minutes * 60
    _text(
        win,
        "nvc_operator_elapsed",
        f"Total elapsed time: {minutes:02d}min {seconds:06.3f}sec",
        pos=(width * 0.245, -height * 0.43),
        height=height * 0.026,
        color=BLACK,
        align="right",
        wrap_width=width * 0.46,
        max_width=width * 0.46,
        max_height=height * 0.075,
    ).draw()
