"""Display 1/2에 표시되는 16:9 Wisecoco 게임 화면."""

from .config import (
    ANSWER_INDICATOR_BLINK_HZ,
    GRAY,
    BLACK,
    GREEN,
    RED,
    SKY_BLUE,
    WHITE,
    WISECOCO_ACTION_AREA_RATIO,
    WISECOCO_DIVIDER_WIDTH,
    WISECOCO_MAIN_AREA_RATIO,
)
from .screens import _line, _outline, _rect, _text


# Display 1/2 in-game 중앙 단어: 기존 length dimension의 2배.
WORD_TEXT_HEIGHT_RATIO = 0.055 * 2
ACTION_TEXT_HEIGHT_RATIO = 0.050
WAIT_TEXT_HEIGHT_RATIO = 0.041
BUTTON_HINT_TEXT_HEIGHT_RATIO = 0.032


def _layout(win) -> tuple[float, float, float, float, float, float]:
    """폭 2:1의 main/action 영역 좌표와 크기를 반환한다."""
    width = float(win.size[0])
    height = float(win.size[1])
    main_width = width * WISECOCO_MAIN_AREA_RATIO
    action_width = width * WISECOCO_ACTION_AREA_RATIO
    main_center_x = -width / 2 + main_width / 2
    action_center_x = width / 2 - action_width / 2
    divider_x = -width / 2 + main_width
    return height, main_width, action_width, main_center_x, action_center_x, divider_x


def _draw_base(win, word: str) -> tuple[float, float, float, float, float, float]:
    height, main_width, action_width, main_x, action_x, divider_x = _layout(win)
    width = float(win.size[0])
    _rect(win, "wc_main_gray", main_width, height, (main_x, 0), GRAY).draw()
    _rect(win, "wc_action_gray", action_width, height, (action_x, 0), GRAY).draw()
    _line(
        win,
        "wc_vertical_divider",
        (divider_x, -height / 2),
        (divider_x, height / 2),
        SKY_BLUE,
        WISECOCO_DIVIDER_WIDTH,
    ).draw()
    _text(
        win,
        "wc_word",
        word,
        pos=(main_x, 0),
        height=height * WORD_TEXT_HEIGHT_RATIO,
        color=BLACK,
        wrap_width=main_width * 0.85,
        bold=False,
    ).draw()
    return width, height, main_width, action_width, main_x, action_x


def _draw_button_mode_base(win, word: str, hint: str) -> tuple[float, float]:
    """터치 panel 없이 전체 화면에 단어와 물리 버튼 hint를 그린다."""
    width = float(win.size[0])
    height = float(win.size[1])
    _rect(win, "wc_button_full_gray", width, height, (0, 0), GRAY).draw()
    _text(
        win, "wc_button_hint", hint, pos=(0, height * 0.43),
        height=height * BUTTON_HINT_TEXT_HEIGHT_RATIO, color=WHITE,
        wrap_width=width * 0.92,
    ).draw()
    _text(
        win, "wc_button_word", word, pos=(0, 0),
        height=height * WORD_TEXT_HEIGHT_RATIO, color=BLACK,
        wrap_width=width * 0.85,
    ).draw()
    return width, height


def _draw_button_mode_game(
    win,
    *,
    game: str,
    activation: bool,
    word: str,
    phase_progress: float,
) -> None:
    hint = (
        "흰 버튼: 차례넘기기    빨강 버튼: 정답시도"
        if game == "verbal"
        else "빨강 버튼: 정답시도"
    )
    width, height = _draw_button_mode_base(win, word, hint)
    if activation:
        if game == "verbal":
            _rect(win, "wc_button_active_green", width, height, (0, 0), GREEN).draw()
        else:
            progress = max(0.0, min(1.0, phase_progress))
            green_height = height * (1.0 - progress)
            if green_height > 0:
                green_y = -height / 2 + green_height / 2
                _rect(
                    win, "wc_button_active_green", width, green_height,
                    (0, green_y), GREEN,
                ).draw()
        # activation tile이 base를 덮으므로 hint와 단어를 마지막에 다시 그린다.
        _text(
            win, "wc_button_active_hint", hint, pos=(0, height * 0.43),
            height=height * BUTTON_HINT_TEXT_HEIGHT_RATIO, color=WHITE,
            wrap_width=width * 0.92,
        ).draw()
        _text(
            win, "wc_button_active_word", word, pos=(0, 0),
            height=height * WORD_TEXT_HEIGHT_RATIO, color=BLACK,
            wrap_width=width * 0.85,
        ).draw()
    else:
        wait_message = (
            "상대가 차례를 넘길 때까지 기다리세요"
            if game == "verbal"
            else "상대의 차례가 끝날 때까지 기다리세요"
        )
        _text(
            win, "wc_button_wait", wait_message, pos=(0, -height * 0.35),
            height=height * WAIT_TEXT_HEIGHT_RATIO, color=WHITE,
            wrap_width=width * 0.88,
        ).draw()


def draw_verbal_activation_positive(win, word: str) -> None:
    """Verbal Activation(+): 설명 차례이며 두 터치 선택지가 보이는 화면."""
    width, height, main_width, action_width, main_x, action_x = _draw_base(win, word)
    divider_x = -width / 2 + main_width
    _rect(win, "wc_verbal_active_green", main_width, height, (main_x, 0), GREEN).draw()
    # 초록 타일이 base text를 덮으므로 단어를 마지막에 다시 그린다.
    _text(
        win, "wc_verbal_active_word", word, pos=(main_x, 0),
        height=height * WORD_TEXT_HEIGHT_RATIO, color=BLACK,
        wrap_width=main_width * 0.85,
    ).draw()
    _line(
        win, "wc_action_horizontal_divider", (divider_x, 0), (width / 2, 0),
        SKY_BLUE, WISECOCO_DIVIDER_WIDTH,
    ).draw()
    _text(
        win, "wc_turn_over", "차례넘기기\n(터치)", pos=(action_x, height / 4),
        height=height * ACTION_TEXT_HEIGHT_RATIO, color=WHITE,
        wrap_width=action_width * 0.85,
    ).draw()
    _text(
        win, "wc_answer_attempt", "정답시도\n(터치)", pos=(action_x, -height / 4),
        height=height * ACTION_TEXT_HEIGHT_RATIO, color=WHITE,
        wrap_width=action_width * 0.85,
    ).draw()


def draw_verbal_activation_negative(win, word: str) -> None:
    """Verbal Activation(-): 상대의 차례를 기다리는 비활성 화면."""
    _, height, _, action_width, _, action_x = _draw_base(win, word)
    _text(
        win,
        "wc_verbal_wait",
        "상대가 차례를 넘길\n때까지 기다리세요",
        pos=(action_x, 0),
        height=height * WAIT_TEXT_HEIGHT_RATIO,
        color=WHITE,
        wrap_width=action_width * 0.88,
    ).draw()


def draw_nonverbal_activation_positive(
    win,
    word: str,
    phase_progress: float,
) -> None:
    """Non-verbal Activation(+): 15초 동안 아래로 사라지는 초록 타일."""
    width, height, main_width, action_width, main_x, action_x = _draw_base(win, word)
    progress = max(0.0, min(1.0, phase_progress))
    green_height = height * (1.0 - progress)
    if green_height > 0:
        green_y = -height / 2 + green_height / 2
        _rect(
            win,
            "wc_nonverbal_active_green",
            main_width,
            green_height,
            (main_x, green_y),
            GREEN,
        ).draw()
    # wipe tile과 관계없이 단어는 유지한다.
    _text(
        win, "wc_nonverbal_active_word", word, pos=(main_x, 0),
        height=height * WORD_TEXT_HEIGHT_RATIO, color=BLACK,
        wrap_width=main_width * 0.85,
    ).draw()
    _text(
        win, "wc_nonverbal_answer_attempt", "정답시도\n(터치)",
        pos=(action_x, 0), height=height * ACTION_TEXT_HEIGHT_RATIO,
        color=WHITE, wrap_width=action_width * 0.85,
    ).draw()


def draw_nonverbal_activation_negative(win, word: str) -> None:
    """Non-verbal Activation(-): 상대의 차례 종료를 기다리는 비활성 화면."""
    _, height, _, action_width, _, action_x = _draw_base(win, word)
    _text(
        win,
        "wc_nonverbal_wait",
        "상대의 차례가 끝날\n때까지 기다리세요",
        pos=(action_x, 0),
        height=height * WAIT_TEXT_HEIGHT_RATIO,
        color=WHITE,
        wrap_width=action_width * 0.88,
    ).draw()


def draw_wisecoco_game_screen(
    win,
    *,
    game: str,
    activation: bool,
    word: str,
    phase_progress: float = 0.0,
    touch_enabled: bool = True,
) -> None:
    """게임 종류와 activation 상태에 맞는 Wisecoco 화면을 그린다."""
    if not touch_enabled:
        _draw_button_mode_game(
            win,
            game=game,
            activation=activation,
            word=word,
            phase_progress=phase_progress,
        )
        return
    if game == "verbal":
        if activation:
            draw_verbal_activation_positive(win, word)
        else:
            draw_verbal_activation_negative(win, word)
    elif game == "nonverbal":
        if activation:
            draw_nonverbal_activation_positive(win, word, phase_progress)
        else:
            draw_nonverbal_activation_negative(win, word)
    else:
        raise ValueError(f"Unknown Wisecoco game type: {game}")


def draw_wisecoco_answer_attempt_indicator(
    win,
    elapsed: float,
    *,
    activation: bool,
) -> None:
    """정답시도 중 Display 1/2 우상단에 상태별 네모를 점멸시킨다."""
    width = float(win.size[0])
    height = float(win.size[1])
    size = min(width, height) * 0.090
    margin = min(width, height) * 0.025
    position = (
        width / 2 - margin - size / 2,
        height / 2 - margin - size / 2,
    )
    first_phase = (
        int(max(0.0, elapsed) * ANSWER_INDICATOR_BLINK_HZ * 2) % 2
        == 0
    )
    if activation:
        fill_color = RED if first_phase else GREEN
        _rect(
            win,
            "wc_answer_blink_active_fill",
            size,
            size,
            position,
            fill_color,
        ).draw()
    elif first_phase:
        _rect(win, "wc_answer_blink_fill", size, size, position, RED).draw()
    else:
        _outline(
            win,
            "wc_answer_blink_outline",
            size,
            size,
            position,
            RED,
            2,
        ).draw()


def draw_verbal_control_sentence_screen(win, sentence: str) -> None:
    """Display 1 전체를 초록색으로 채우고 현재 VC 문장 하나만 표시한다."""
    width = float(win.size[0])
    height = float(win.size[1])
    _rect(win, "vc_sentence_background", width, height, (0, 0), GREEN).draw()
    _text(
        win,
        "vc_sentence",
        sentence,
        pos=(0, 0),
        height=height * 0.060,
        color=BLACK,
        wrap_width=width * 0.86,
        max_width=width * 0.86,
        max_height=height * 0.55,
    ).draw()


def draw_nonverbal_control_instruction_screen(win) -> None:
    """Display 1 NVC 안내를 VC와 같은 위치·글자 규격으로 표시한다."""
    draw_verbal_control_sentence_screen(
        win,
        "진행자의 안내에 따라 동작해주세요",
    )


def _draw_subsidiary_message(win, *, key: str, message: str) -> None:
    """Wisecoco 전체를 회색으로 채우고 중앙 안내문을 표시한다."""
    width = float(win.size[0])
    height = float(win.size[1])
    _rect(win, key + "_background", width, height, (0, 0), GRAY).draw()
    _text(
        win,
        key + "_message",
        message,
        pos=(0, 0),
        height=height * 0.060,
        color=WHITE,
        wrap_width=width * 0.86,
        bold=False,
    ).draw()


def draw_wisecoco_host_adjusting_screen(win) -> None:
    """host 조작 state에서 participant에게 공통 대기 화면을 표시한다."""
    _draw_subsidiary_message(
        win,
        key="wc_host_adjusting_subsidiary",
        message="진행자가 화면을 조정 중...",
    )
