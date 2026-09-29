"""장비, timing, event code, display 및 asset 경로 설정.

Natus Quantum–LabJack 배선:
    Natus TRG1  = LabJack EIO0 = bit 0, Least Significant Bit
    Natus TRG2  = LabJack EIO1 = bit 1
    Natus TRG3  = LabJack EIO2 = bit 2
    Natus TRG4  = LabJack EIO3 = bit 3
    Natus TRG5  = LabJack EIO4 = bit 4
    Natus TRG6  = LabJack EIO5 = bit 5
    Natus TRG7  = LabJack EIO6 = bit 6
    Natus TRG8  = LabJack EIO7 = bit 7, Most Significant Bit
    Natus TRG9  = LabJack CIO0 = latch
    GND         = GND
"""

from pathlib import Path

DEVICE_TYPE = "T4"
CONNECTION_TYPE = "USB"  # USB 연결이면 "USB", Ethernet이면 "ETHERNET"
IDENTIFIER = "ANY"

# LabJack digital lines
DATA_LINES = ["EIO0", "EIO1", "EIO2", "EIO3", "EIO4", "EIO5", "EIO6", "EIO7"]
LATCH_LINE = "CIO0"

# Trigger timing
PULSE_WIDTH_SEC = 0.020  # latch high duration: 20 ms
SETUP_TIME_SEC = 0.002   # data bits를 먼저 올려둔 뒤 latch까지 대기
HOLD_TIME_SEC = 0.002    # latch를 내린 뒤 data bits를 잠깐 유지
PHOTODIODE_FLASH_FRAMES = 4
ANSWER_INDICATOR_BLINK_HZ = 1.3

# 8-bit event code. 0은 data-line idle이며 전체 정의는 codebook.md가 기준이다.

# --- 시스템 / 내비게이션 ---
CODE_SELECT_GAME_ENTER = 1
CODE_SELECT_NAMEGAME = 2
CODE_SELECT_BODYGAME = 3
# code 4는 이전 Nonverbal Control 직접 진입 event와의 구분을 위해 예약한다.
CODE_EXIT_REQUEST = 5
CODE_EXIT_YES = 6
CODE_EXIT_NO = 7

# --- NameGame ---
CODE_NAME_FIRST_RIGHT = 10
CODE_NAME_FIRST_LEFT = 11
CODE_NAME_GAME_START = 12
CODE_NAME_TRY_RIGHT = 13
CODE_NAME_TRY_LEFT = 14
CODE_NAME_TRY_YES = 15
CODE_NAME_TRY_NO = 16
CODE_NAME_TRY_CANCEL = 17
CODE_NAME_TURN_TO_RIGHT = 18
CODE_NAME_TURN_TO_LEFT = 19

# --- 몸으로말해요 ---
CODE_BODY_FIRST_RIGHT = 20
CODE_BODY_FIRST_LEFT = 21
CODE_BODY_GAME_START = 22
CODE_BODY_TRY_RIGHT = 23
CODE_BODY_TRY_LEFT = 24
CODE_BODY_TRY_YES = 25
CODE_BODY_TRY_NO = 26
CODE_BODY_TRY_CANCEL = 27
CODE_BODY_AUTO_TO_RIGHT = 28
CODE_BODY_AUTO_TO_LEFT = 29

# --- R 재설정 / 선택 화면 복귀 ---
CODE_RESET_NAME_ORDER = 30
CODE_RESET_BODY_ORDER = 31
CODE_RESET_NAME_START = 32
CODE_RESET_BODY_START = 33
CODE_RESET_EXIT = 34

# --- Control 확인 / PASS ---
CODE_VERBAL_CONTROL_CONFIRM = 40
CODE_NAME_PASS_RIGHT = 41
CODE_NAME_PASS_LEFT = 42
CODE_BODY_PASS_RIGHT = 43
CODE_BODY_PASS_LEFT = 44

# --- Verbal Control ---
CODE_VERBAL_CONTROL_START = 50
CODE_VERBAL_CONTROL_CANCEL = 51
CODE_VERBAL_CONTROL_NEXT = 52
CODE_VERBAL_CONTROL_PREVIOUS = 53
CODE_VERBAL_CONTROL_FINISH = 54
CODE_VERBAL_CONTROL_RETURN = 55
CODE_VERBAL_CONTROL_GAME_SELECT = 56

# --- Nonverbal Control ---
CODE_NONVERBAL_CONTROL_CONFIRM = 60
CODE_NONVERBAL_CONTROL_START = 61
CODE_NONVERBAL_CONTROL_CANCEL = 62
CODE_NONVERBAL_CONTROL_FINISH = 63
CODE_NONVERBAL_CONTROL_RETURN = 64
CODE_NONVERBAL_CONTROL_GAME_SELECT = 65

# --- 게임 timing ---
BODY_EXPLAIN_DURATION_SEC = 15.0   # 몸으로말해요 자동 차례전환 주기

# 몸으로말해요 전용 sound effects
BASE_DIR = Path(__file__).resolve().parents[1]
SOUNDS_DIR = BASE_DIR / "sounds"
VERBAL_CONTROL_SCRIPT_PATH = BASE_DIR / "verbal_control_script.txt"

# Word-list
WORD_LIST_SET = "utensil"
WORD_LISTS_DIR = BASE_DIR / "word_lists"
WORD_LIST_FILE_PREFIX = "word_list_"
WORD_LIST_FILE_SUFFIX = ".txt"

BODY_SOUND_PATH = SOUNDS_DIR / "BODY_SOUND.mp3"
STATE_TRANSITION_SOUND_CODES = frozenset({12, 22, 50, 61})
STATE_TRANSITION_TONE_HZ = 440
STATE_TRANSITION_TONE_DURATION_SEC = 0.1
# 기존 BODY_SOUND peak 일치 gain의 1/2에서 다시 0.7배로 조정.
STATE_TRANSITION_TONE_GAIN = (0.3386055827140808 / 2) * 0.7
AUDIO_OUTPUT_DEVICE_NAME = "스피커(Realtek(R) Audio)"

# Terminal log
TASK_DONE_TEXTS_DIR = BASE_DIR / "task_done_texts"
TASK_DONE_FILE_PREFIX = "task_done_"
TASK_DONE_FILE_SUFFIX = ".txt"

LOG_TIMESTAMP_FOR_FILENAME_FORMAT = "%Y-%m-%d_%H-%M-%S"
LOG_TIMESTAMP_FOR_TEXT_FORMAT = "%Y-%m-%d %H:%M:%S"

# Windows 확장 display 순서와 일치해야 한다.
DISPLAY_0_INDEX = 0  # laptop / operator display
DISPLAY_1_INDEX = 1  # first Wisecoco touchscreen
DISPLAY_2_INDEX = 2  # second Wisecoco touchscreen

# 실물 fullscreen은 native size, 아래 값은 mock-up 종횡비 기준이다.
DISPLAY_0_SIZE = (1440, 900)
DISPLAY_1_SIZE = (1920, 1080)
DISPLAY_2_SIZE = (1920, 1080)

WINDOW_BACKEND = "pyglet"  # screen 번호 지정 및 multiple Window 지원
FULLSCREEN = True
COLOR_SPACE = "rgb"

# Wisecoco main area : action area = 2 : 1
WISECOCO_MAIN_AREA_RATIO = 2.0 / 3.0
WISECOCO_ACTION_AREA_RATIO = 1.0 / 3.0
WISECOCO_DIVIDER_WIDTH = 2.5

GRAY = [0.0, 0.0, 0.0]
RED = [1.0, -1.0, -1.0]
GREEN = [-1.0, 1.0, -1.0]
SKY_BLUE = [-0.2, 0.6, 1.0]
ORANGE = [1.0, 0.1, -1.0]
BLACK = [-1.0, -1.0, -1.0]
WHITE = [1.0, 1.0, 1.0]

FONT_NAME = "Malgun Gothic"
