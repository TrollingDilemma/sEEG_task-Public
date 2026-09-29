# sEEG Task Runner — Control + NameGame + 몸으로말해요

## 프로젝트 개요

PsychoPy로 Display 0(진행자 노트북)과 Display 1/2(Wisecoco 터치스크린)를
제어하고, host 키보드 및 participant touch input을 게임 state transition으로
변환하는 Windows용 sEEG 과제 실행 프로그램입니다.

LabJack T4의 EIO0–EIO7과 CIO0 latch를 통해 Natus Quantum으로 8-bit TTL을
전송합니다. TTL event와 동일한 Display 0 flip에는 4-frame photodiode marker가
표시됩니다.

현재 구현 범위:

| 기능 | 상태 |
|---|---|
| 단어맞추기(NameGame) | 게임 흐름·touch·TTL 구현 완료 |
| 몸으로말해요 | 게임 흐름·15초 전환·sound·touch·TTL 구현 완료 |
| Verbal Control | 실행 확인·10문장 순차 표시·이전/다음 이동·timer·TTL 구현 완료 |
| Nonverbal Control | 안내 화면·timer·Space 종료·TTL 구현 완료 |

각 event code는 게임과 주요 state transition을 구분하도록 설계되어 있습니다.
좌·우 구분이 필요한 시작 side, 정답시도, 차례 전환, PASS는 side별 code를 사용합니다.
전체 정의는 [`codebook.md`](codebook.md)를 참고하세요.

## 목차

### 처음 설치하고 실행하기

1. [빠른 시작](#빠른-시작)
2. [화면 및 장비 연결](#화면-및-장비-연결)
3. [연결 테스트](#연결-테스트)

### 실험 준비와 진행

1. [조작 방법](#조작-방법)
2. [Wisecoco 터치 입력과 Windows 문제 해결](#wisecoco-터치-입력)
3. [게임 흐름](#게임-흐름)
4. [Word-list 선택 및 추가](#word-list-선택-및-추가)
5. [로그](#로그)
6. [전체 Event Code 표](codebook.md)

### 개발·장비 검증 참고

1. [저장소 구조](#저장소-구조)
2. [내부 실행 구조](#내부-실행-구조)
3. [화면 해상도와 반응형 배치](#화면-해상도와-반응형-배치)
4. [화면·Sound·TTL 동기화](#화면soundttl-동기화)
5. [Display 0 photodiode marker](#display-0-photodiode-marker)
6. [세 사건의 시간 관계](#세-사건의-시간-관계)

## 빠른 시작

처음 실행할 때의 최소 순서입니다. 세부 설명과 문제 해결 방법은 각 링크를
참고하십시오.

1. Windows에 Python 3.10 64-bit를 설치합니다. 실제 LabJack을 사용할 경우
   LabJack LJM Driver도 설치합니다.
2. 프로젝트 루트의 PowerShell에서 가상환경을 설치합니다.

   ```powershell
   python setup_venv.py
   ```

   설치 후 IDE interpreter는 `.venv (Python 3.10, 64-bit)`로 지정합니다.

3. Wisecoco 두 대를 모두 연결할 경우 Windows 디스플레이 모드를
   **이 디스플레이에 확장**으로 설정합니다.
4. 화면 번호와 TTL 연결을 시험합니다.

   ```powershell
   .\.venv\Scripts\python.exe -m tests.display_test
   .\.venv\Scripts\python.exe -m tests.connection_test
   ```

5. 실제 과제를 실행합니다.

   ```powershell
   .\.venv\Scripts\python.exe main.py
   ```

LabJack이 없을 때는 확인 dialog를 거쳐 MOCK-UP으로 실행할 수 있습니다.
Wisecoco는 두 대 모두 연결하거나 모두 분리해야 하며, 한 대만 연결한 구성은
지원하지 않습니다.

## 저장소 구조

```text
.
├─ main.py                  # 실행 진입점
├─ setup_venv.py            # Python 3.10 가상환경 설치 스크립트
├─ requirements.txt
├─ codebook.md              # TTL event code 단일 기준 문서
├─ verbal_control_script.txt  # Verbal Control 문장 10개
├─ tests/                   # 장비 연결·화면 출력·PNG 검수 스크립트
│  ├─ connection_test.py
│  ├─ control_state_test.py
│  ├─ cursor_macro_test.py
│  ├─ touch_calibration_test.py
│  ├─ display_test.py
│  └─ render_wisecoco_previews.py
├─ sounds/
│  └─ BODY_SOUND.mp3
├─ word_lists/
│  └─ word_list_utensil.txt # 한 줄당 한 단어, 1개 이상의 고유 단어
├─ task/
│  ├─ app.py                # 장비 setup + 최상위 실행 loop
│  ├─ input_router.py       # host keyboard + touch 입력 통합
│  ├─ control_state.py      # Control 문장 load/validation + 입력 전이
│  ├─ cursor_macro.py       # Display 0 중앙으로 Windows cursor 이동
│  ├─ touch_calibration.py  # touch 사용 선택 + Windows 설정 macro
│  ├─ word_state.py         # 좌·우 독립 permutation/index
│  ├─ word_list_selector.py # 최대 4열 word-list grid 배치
│  ├─ game_state.py         # state transition, timer, turn, event code
│  ├─ display_router.py     # Display 0/1/2 draw + flip routing
│  ├─ touch_input.py        # pyglet touch-down callback + 좌표 판정
│  ├─ config.py             # LabJack/TTL code/타이밍/화면 설정
│  ├─ ljm_backend.py        # 실제 LabJack <-> MOCK 전환 프록시
│  ├─ ttl.py                # flip 동기 TTL trigger 전송
│  ├─ screens.py            # 반응형 PsychoPy draw + TextStim 자동 축소/캐시
│  ├─ operator_screens.py   # Display 0 monitoring 화면
│  ├─ wisecoco_screens.py   # Display 1/2 게임 화면
│  ├─ sounds.py             # sound file 사전 load
│  ├─ words.py              # txt word-list load/validation/permutation
│  ├─ state_utils.py        # turn 기록 (duration 포함)
│  ├─ logger.py             # 터미널 + txt 동시 로그
│  └─ models.py             # 공유 데이터 모델
└─ task_done_texts/         # 실행 로그 (.txt, git 미추적)
```

## 내부 실행 구조

정식 실행 진입점은 프로젝트 루트의 `main.py` 하나입니다. `task/` 내부 파일은
직접 실행하지 않고 package module로 import합니다.

```text
main.py
├─ task.logger
└─ task.app
   ├─ InputRouter ──> TouchInputRouter
   │                 └─ CursorMacro
   ├─ GameState ────> WordState + ControlState
   ├─ DisplayRouter ─> operator/wisecoco/screens
   ├─ DisplayWindows
   └─ FlipSynchronizedTrigger ─> LabJack backend
```

한 frame의 실행 방향은 다음과 같이 고정되어 있습니다.

```text
InputRouter.poll()
→ GameState.step()
→ DisplayRouter.render()
→ DisplayRouter.present()  # Display flip + sound + TTL
```

`config.py`와 `models.py`는 하위 공통 모듈이며 router나 `app.py`를 import하지
않습니다. 내부 task module 간 순환 import는 허용하지 않습니다.

### 내부 renderer의 반응형 처리

`screens.py`의 공통 TextStim cache와 자동 축소 처리를 Display 0/1/2가 함께
사용합니다. 해상도 인식, safe area, mock-up 종횡비와 검증 해상도에 관한 상세
설명은 [화면 해상도와 반응형 배치](#화면-해상도와-반응형-배치)에서 한 번만
관리합니다.

책임 경계는 다음과 같습니다.

| 변경 대상 | 담당 모듈 |
|---|---|
| 키 binding 및 touch-action 변환 | `input_router.py` |
| 상단 숫자열 `0` 감지와 Windows cursor 이동 | `cursor_macro.py` |
| 시작 전 touch mode 선택과 Windows 설정 도구 실행 | `touch_calibration.py` |
| touch callback과 좌표 경계 | `touch_input.py` |
| 공통 게임·종료 state 전이 | `game_state.py` |
| VC/NVC 문장·cursor·입력 전이 | `control_state.py` |
| 좌·우 단어 permutation/index | `word_state.py` |
| word-list grid 행·열 배치 | `word_list_selector.py` |
| Display 0/1/2 화면 선택 | `display_router.py` |
| 화면의 실제 도형·문구 | `operator_screens.py`, `wisecoco_screens.py`, `screens.py` |
| flip 기준 TTL pulse | `ttl.py` |

시험 스크립트는 import 경로 문제를 피하기 위해 프로젝트 루트에서
`python -m tests.<module>` 형식으로 실행합니다.

장비 없이 실행할 수 있는 로직 검사:

```powershell
python -m tests.control_state_test
python -m tests.cursor_macro_test
python -m tests.touch_calibration_test
```

## Word-list 선택 및 추가

단어 목록은 프로젝트의 `word_lists/` 폴더에 저장하며 파일명은 반드시
`word_list_<목록이름>.txt` 형식을 사용합니다. `task/config.py`의
`WORD_LIST_SET`은 아직 선택 화면을 거치지 않은 내부 기본 목록입니다.

```python
WORD_LIST_SET = "utensil"  # word_lists/word_list_utensil.txt
```

새 목록을 추가하고 실행 중 선택하는 순서는 다음과 같습니다.

1. `word_lists/word_list_emotion.txt`처럼 새 txt 파일을 생성합니다.
2. 한 줄당 한 단어씩 고유 단어를 1개 이상 입력하고 UTF-8로 저장합니다.
3. 게임 순서 선택 다음에 Display 0의 word-list 선택 grid로 이동합니다.
4. `word_list_*.txt` 상자를 좌·우 방향키로 선택하고 Enter를 누릅니다.
5. 선택 완료 후 `start_confirm` 화면으로 이동합니다.

프로그램은 `word_lists/word_list_*.txt`를 실행 시 자동 검색합니다. 파일이 하나뿐이면
grid에도 해당 항목 하나만 표시됩니다. 선택 화면에 진입할 때는 항상 정렬된 목록의
맨 왼쪽 첫 항목을 sky-blue로 강조합니다. 최종 사용 목록은 매 game session 직전에
Enter로 선택합니다. 목록 선택 화면에서 R을 누르면 해당 게임의 순서 선택 화면으로
돌아갑니다.
상자는 파일 순서대로 최대 4열로 배치되며, 목록이 `4n`개이면 `n×4` grid가 됩니다.
마지막 행이 4개 미만이면 해당 행을 가운데 정렬합니다. 방향키 이동과 Enter 확정에는
별도의 TTL code가 없습니다.

파일명과 기본 선택값의 대응 예시는 다음과 같습니다.

| `WORD_LIST_SET` | 불러오는 파일 |
|---|---|
| `"utensil"` | `word_lists/word_list_utensil.txt` |
| `"emotion"` | `word_lists/word_list_emotion.txt` |

검색된 파일은 UTF-8 txt, 한 줄당 한 단어, 비어 있지 않은 고유 단어 정확히
1개 이상인지 프로그램 시작 시 검증합니다. 단어 수의 상한은 없습니다. 빈 줄은
단어 수에 포함하지 않으며,
파일 누락·단어 수 오류·중복이 있으면 실행 초기에 오류가 발생합니다.

## 화면 및 장비 연결

Wisecoco 두 대를 사용할 때는 먼저 Windows의
`시스템 → 디스플레이 → 다중 디스플레이`에서 바탕 화면을
**`이 디스플레이에 확장`**으로 설정해야 합니다. 화면 복제 모드는 지원하지
않으며, 노트북과 Wisecoco 두 대가 서로 독립된 세 display로 인식되어야 합니다.

LabJack과 display 연결 상태에 따른 실행 방식은 다음과 같습니다.

| LabJack | Windows가 인식한 화면 | 동작 |
|---|---:|---|
| 연결됨 | 3개 이상 | 세 물리 display fullscreen + 실제 TTL |
| 연결됨 | 1개 또는 2개 | 노트북 `DISPLAY 0/1/2` 3분할 MOCK-UP + 실제 TTL |
| 연결 실패 | 1개 또는 2개 | 확인 dialog 후 노트북 `DISPLAY 0/1/2` 3분할 MOCK-UP; 실제 TTL 없음 |
| 연결 실패 | 3개 이상 | 확인 dialog 후 세 물리 display 출력; MOCK backend로 실제 TTL 없음 |

LabJack 없이 진행할지 묻는 확인 dialog에서 Cancel을 누르면 종료됩니다.
물리 screen이 3개 미만이면 touch mapping 도구를 건너뛰고 자동으로 노트북
3분할 mock-up을 사용합니다. LabJack이 연결되어 있으면 실제 TTL은 유지합니다.

## 조작 방법

| 키 | 기능 |
|---|---|
| ← / → | 선택지 이동 (게임·순서·word list·정오답·Control 종료·종료 확인) |
| Enter | 선택 확정 / 게임 시작 / 정답시도 / 정오답 확정 |
| Space | NameGame 차례 넘김 / VC 다음 문장 / NVC 종료 |
| Y / N | 정오답 직접 확인 |
| Backspace | VC 이전 문장 / Control 종료화면에서 복귀 |
| P | activated(+) side 자신의 단어 PASS (host 전용) |
| 키보드 상단 숫자열 `0` | mouse cursor를 Display 0 정중앙으로 이동 |
| R | 재설정 (화면별 행선지는 `codebook.md` 참고) |
| Ctrl+Q | 종료 확인 |

Ctrl+Q 종료 확인 화면에는 `프로그램을 완전 종료할까요?` 문구와
`예`, `아니오`, `게임 고르기` 가로 상자가 표시됩니다. 좌·우 방향키 이동에는
TTL이 없으며 Enter 확정 시 각각 code 6, 7, 34가 발생합니다. 기본 선택은
`아니오`입니다.

VC 마지막 문장 또는 NVC 종료 Space로 진입하는 `control_finish`는 Ctrl+Q
종료확인과 별개의 화면입니다. `control이 끝났습니다\n\n다음 중 고르세요` 문구와
`control로 돌아가기`, `게임 고르기` 두 상자를 표시하며, 좌·우 방향키와 Enter로
선택합니다.

Wisecoco 터치 후 pointer가 Display 1/2로 이동했을 때 host가 키보드 상단
숫자열의 `0`을 누르면 pointer를 Display 0 Window의 실제 client area 정중앙으로 즉시
되돌립니다. 이 macro는 모든 state에서 사용할 수 있으며 state transition, 화면
flip, TTL 및 별도 로그를 발생시키지 않습니다. 이 binding은 우측 numeric
keypad의 Num 0이 아니라, `1`부터 `0`까지 가로로
배치된 키보드 상단 숫자열의 `0`입니다. 우측 Num 0과 Insert는 macro를 실행하지
않습니다. 다중 PsychoPy Window에서 keyboard event가 누락되는 경우에도
동작하도록 Windows `GetAsyncKeyState`로 상단 `0`의 `VK_0` key-down edge를
직접 확인합니다.
이동 시 cursor clipping을 해제하고 `SetCursorPos` 결과 좌표도 다시 읽어
Display 0 client 중앙 도달 여부를 검증합니다.

### Wisecoco 터치 입력

#### 시작 전 touch mode 선택 (`touch_calibration.py`)

`main.py`는 참가자 이름 입력과 게임 Window 생성 전에
`task.touch_calibration`을 실행합니다.

| 선택창 항목 | 내부값 | 실행되는 Windows 도구 | 결과 |
|---|---:|---|---|
| `1. 터치기능 미사용(버튼 사용)` | `1` | 실행하지 않음 | 즉시 물리 버튼 모드 |
| `2. 터치기능 사용` | `2` | MultiDigiMon touch mapping | Display 0/1/2 매핑 후 터치 모드 |

선택값 2만 PowerShell의 `Start-Process -Verb RunAs`를 통해 다음 mapping
도구를 관리자 권한으로 실행합니다. 선택값 1은 UAC와 mapping을 모두 생략합니다.

```text
MultiDigiMon.exe -touch
```

mapping wizard를 열기 전 안내 dialog에는
**“물리 mapping을 완료하십시오.”**를 표시합니다. `OK`를 누르면 물리 mapping wizard가 직접
실행됩니다. 이때 Windows 사용자 계정 컨트롤(UAC) 창에서 `예`를 눌러야 하며,
wizard가 종료될 때까지 프로그램이 기다립니다. 물리 mapping은
진행자가 완료해야 합니다.

`MultiDigiMon` 자체는 정상적으로 mapping을 마친 뒤에도 exit code 1을 반환할 수
있으므로 해당 child exit code는 게임 중단 조건으로 사용하지 않습니다. UAC 실행
자체가 거부되거나 시작하지 못한 경우에만 session을 종료합니다.

선택값 1은 `False`, 선택값 2는 `True`를 반환합니다. Cancel 또는 도구 실행
실패는 `None`을 반환합니다. 이 경우
참가자 이름 dialog, LabJack 연결, Display Window 및 게임 loop를 시작하지 않고
현재 session을 종료합니다. 시작 선택에는 TTL이 없습니다.

이 선택창만 별도로 실행하려면 프로젝트 루트에서 다음을 사용합니다.

```powershell
python -m task.touch_calibration
```

#### Windows에서 touch input과 물리 display 매핑하기

화면 출력은 Display 1/2에 정상적으로 나오지만 터치한 위치가 노트북이나 반대쪽
Wisecoco의 click으로 들어오면, PsychoPy를 실행하기 전에 Windows의 touch input
출처와 물리 display를 다시 연결해야 합니다.

1. 노트북과 Wisecoco 두 대를 모두 연결합니다. HDMI/DisplayPort뿐 아니라 각
   Wisecoco의 touch용 USB 케이블도 연결합니다.
2. Windows `설정 → 시스템 → 디스플레이`에서 세 화면을
   **이 디스플레이에 확장**으로 설정합니다. 화면 복제 상태에서는 진행하지 않습니다.
3. `main.py` 시작 선택창에서 원하는 터치 모드를 고르거나, `Win+R`을
   누르고 다음 명령을 직접 실행합니다.

   ```text
   MultiDigiMon.exe -touch
   ```

4. 흰색 물리 display 식별 화면이 순서대로 표시됩니다.

   - 안내가 표시된 화면이 touch screen이 아니면 `Enter`를 눌러 다음 화면으로
     이동합니다.
   - 안내가 실제 Wisecoco에 표시되면 **그 Wisecoco 화면을 직접 한 번 터치**합니다.
   - Display 1과 Display 2가 각각 올바른 touch 장치에 대응할 때까지 화면 안내를
     따라 진행합니다.
   - 잘못 선택했으면 `Esc`로 취소한 뒤 처음부터 다시 수행합니다.

5. 좌표 보정까지 필요하면 별도로 Tablet PC Settings를 열고 각 Wisecoco에서
   `보정(Calibrate)`을 실행합니다. Mapping은 touch 장치와 monitor의 대응을,
   Calibrate는 해당 화면 내부의 좌표 정확도를 맞추는 작업입니다.
6. 바탕화면에서 Wisecoco 두 대를 각각 한 번씩 터치하여 pointer가 **터치한 바로
   그 화면과 위치**에 나타나는지 확인한 후 `main.py`를 실행합니다.

이 설정은 Windows의 장치–monitor 매핑입니다. `DISPLAY_1_INDEX`와
`DISPLAY_2_INDEX`는 영상 출력 Window의 위치를 정하며, 잘못된 Windows touch
매핑을 Python 좌표 계산만으로 교정할 수는 없습니다.

#### device manager에서 touch input 자체를 끄기

ghost touch, 반대 화면 입력 또는 장치 식별 문제를 분리 진단할 때는 특정 touch
장치를 임시로 비활성화할 수 있습니다. touch를 끄더라도 일반적으로 HDMI/DisplayPort
영상 출력은 유지되고 해당 USB HID touch 입력만 중단됩니다.

1. 프로그램 밖에서 `Win+X → 장치 관리자(Device Manager)`를 직접 엽니다.
2. `휴먼 인터페이스 장치(Human Interface Devices)`를 펼칩니다.
3. `HID 규격 터치 스크린(HID-compliant touch screen)`을 찾습니다.
4. 대상 항목을 우클릭하고 `디바이스 사용 안 함(Disable device)`을 선택한 뒤
   확인합니다.
5. 해당 Wisecoco를 터치하여 입력이 실제로 중단됐는지 확인합니다.
6. 다시 사용하려면 같은 항목을 우클릭하고
   `디바이스 사용(Enable device)`을 선택합니다.

주의사항:

- `제거(Uninstall device)`가 아니라 **사용 안 함(Disable device)**을 사용합니다.
- 항목이 여러 개이면 Windows가 어느 항목이 Display 1/2인지 이름만으로 명확히
  보여주지 않을 수 있습니다. 한 번에 하나만 비활성화하고 두 화면을 각각 터치하여
  대응 관계를 기록하십시오.
- 더 확실히 구분하려면 프로그램을 종료한 상태에서 한 Wisecoco의 touch USB
  케이블만 분리하여 사라지는 HID 항목을 확인합니다. 영상 케이블과 touch USB
  케이블을 혼동하지 마십시오.
- 모든 `HID-compliant touch screen` 항목을 끄면 Display 1/2의 터치 게임 입력을
  사용할 수 없습니다. 이 방법은 문제 장치 격리 또는 touch를 의도적으로 사용하지
  않을 때만 사용합니다.
- 장치 비활성화·재활성화 또는 USB 재연결 후에는 `main.py`를 완전히 종료했다가
  다시 실행하여 pyglet Window의 input handler를 새로 등록합니다.

참고:

- [Microsoft Support: Windows에서 터치스크린 사용 및 사용 안 함](https://support.microsoft.com/en-US/Windows/hardware/input-devices/enable-and-disable-a-touchscreen-in-windows)

#### 프로그램 내부 touch 처리

Windows가 전달하는 단일 touch-down을 각 Wisecoco pyglet Window의 press callback에서
즉시 수집한 뒤 PsychoPy local pixel 좌표로 변환합니다. 터치는 activated(+) side에서만
동작하며, 화면의 SKY_BLUE 세로선 오른쪽부터 화면 끝까지를 action 영역으로 판정합니다.
SKY_BLUE 세로선과 NameGame의 가로선 자체는 입력 영역에서 제외됩니다.

| 화면 | 터치 영역 | 동작 |
|---|---|---|
| NameGame activated(+) | 오른쪽 action 영역 위쪽 | 차례넘기기 |
| NameGame activated(+) | 오른쪽 action 영역 아래쪽 | 정답시도 |
| 몸으로말해요 activated(+) | 오른쪽 action 영역 전체 | 정답시도 |
| activated(-) 또는 host 조작 화면 | 모든 영역 | 입력 무시 |

터치 한 번은 touch-down callback 한 건으로 처리하므로 누르고 있는 동안 반복되지 않고,
짧은 단일 터치도 release 전에 queue에 저장됩니다. 터치 좌표와 action은 별도
로그로 남기지 않고 처리 결과에 해당하는 TTL 행만 기록합니다. PASS는 터치에
연결되지 않으며 Display 0의 host `P` 키만 사용합니다.

`1. 터치기능 미사용(버튼 사용)`에서는 touch callback을 action으로 변환하지
않습니다. Display 1/2의 우측 touch panel과 sky-blue 세로 구분선을 제거하고
전체 폭 게임 화면을 사용합니다. 각 화면 최상단 hint는 다음과 같습니다.

- NameGame: `흰 버튼: 차례넘기기    빨강 버튼: 정답시도`
- 몸으로말해요: `빨강 버튼: 정답시도`

### 게임 흐름

```
게임 선택:
  Verbal Control → 진행 확인 → verbal_control 또는 select_game
  Nonverbal Control → 진행 확인 → nonverbal_control 또는 select_game
  단어맞추기 → 순서 선택 → word list 선택 → 시작 확인 → 본게임
  몸으로말해요 → 순서 선택 → word list 선택 → 시작 확인 → 본게임

NameGame: 본게임 Enter/정답시도 터치 → activated side 정답시도 → 정답 확인
몸으로말해요: 본게임 Enter/정답시도 터치 → activated side 정답시도 → 정답 확인
정답/오답 모두 원래 게임으로 복귀, 차례 유지
```

내부 state와 화면 단계의 대응은 다음과 같습니다. TTL의 단일 기준표는 중복을
피하기 위해 [`codebook.md`](codebook.md)에만 유지합니다.

| state | 역할 |
|---|---|
| `select_game` | 네 가지 게임/Control 선택 |
| `verbal_control_confirm` | Verbal Control 실행 여부 확인 |
| `nonverbal_control_confirm` | Nonverbal Control 실행 여부 확인 |
| `verbal_control` | Display 1에 문장을 순서대로 제시하는 Control 진행 |
| `nonverbal_control` | Display 1에 동작 안내를 표시하는 Control 진행 |
| `name_order` / `body_order` | 먼저 시작할 participant 선택 |
| `name_word_list` / `body_word_list` | 이번 session의 word list 선택 |
| `name_start_confirm` / `body_start_confirm` | 참가자·순서·목록 확인 후 시작 |
| `name_game` / `body_game` | 본게임 진행 및 Display 0/1/2 monitoring |
| `try_answering` | 직전 in-game 화면 유지 + Display 1/2 우상단 점멸 indicator + Display 0 정답 여부 확인 |
| `control_finish` | VC/NVC 정상 완료 후 control 복귀 또는 게임 고르기 선택 |
| `exit_confirm` | `Ctrl+Q` 이후 예·아니오·게임 고르기 선택 |

- `select_game`에는 숫자 prefix 없이 `Verbal Control`, `Nonverbal Control`,
  `단어맞추기`, `몸으로말해요` 네 상자를 가로로 표시합니다.
- 좌·우 방향키로 네 선택지를 순환하며 방향키 이동에는 TTL이 없습니다.
- Verbal Control 선택 시 `Verbal Control을 진행할까요?` 확인 화면이 나타납니다.
  좌·우 방향키로 `예`/`아니오`를 고르고 Enter로 확정합니다.
- Nonverbal Control 선택 시 `Nonverbal Control을 시작할까요?` 확인 화면이
  나타납니다. 같은 `← → 이동    Enter 확정    Ctrl+Q 종료` hint와 입력 방식을
  사용하며, `예`에서만 session timer와 NVC 화면을 시작합니다.
- `예`를 누르면 `verbal_control_script.txt`의 비어 있지 않은 문장 10개를
  Display 1 중앙에 파일 순서대로 하나씩 표시합니다. Display 1은 초록색
  fullscreen 배경과 검은색 문장을 사용하고, Display 2는
  `진행자가 화면 조정 중` 화면을 유지합니다.
- Display 0 중앙에는
  `space: 문장 넘기기    backspace: 문장 되돌리기`를 흰색으로 표시하고,
  우하단에는 검은색 `Total elapsed time: xxmin xx.xxxsec` timer를 표시합니다.
  확인 화면에서 `예`를 누른 순간 timer와 첫 문장 표시가 함께 시작됩니다.
- Space는 다음 문장, Backspace는 이전 문장으로 이동합니다. 첫 문장에서
  Backspace를 누르면 첫 문장을 유지합니다. 열 번째 문장에서 Space를 누르면
  Control 전용 종료화면으로 이동합니다.
- Nonverbal Control 선택 후 Display 0에는 회색 배경,
  중앙의 흰색 `동작을 수행하도록 안내하세요` 및
  `Space: Nonverbal Control 종료` 문구, 우하단의 검은색 session timer를
  표시합니다. Display 1과 2에는 VC와 같은 위치·글자 크기로 초록 배경 중앙에
  검은색 `진행자의 안내에 따라 동작해주세요`를 동일하게 표시합니다.
- NVC에서 Space를 누르면 timer 갱신을 멈춘 채 Control 전용 종료화면으로
  이동합니다. 이 화면에서 Backspace는 NVC를 재개하고, Space는 `select_game`에
  진입합니다. 종료화면 체류 시간은 복귀한 timer에서 제외됩니다.
- 몸으로말해요: 15초마다 설명 차례 자동 전환 (화면·효과음·TTL 동기 송출)
- PASS: activated(+) side 자신의 word index를 진행합니다.
- 정답: activated(+) side가 맞힌 상대 side의 word index를 진행합니다.
- Display 1은 left permutation, Display 2는 right permutation을 항상 표시합니다.
- 다음 index의 단어가 상대 Display의 현재 단어와 같으면 그 위치를 표시하지 않고
  한 칸 더 건너뛰는 `skip_on_conflict` 2-step jump를 적용합니다.
- 정답시도 state에서도 Display 1/2는 직전 in-game 화면을 유지합니다. 정답시도한
  activation(+) 화면의 우상단 indicator는 빨강/초록 채움을 1.3 Hz로 왕복하고,
  반대편은 빨강 채움/무채움을 왕복합니다. 별도 정답시도 안내문은 없습니다.
- Display 0의 red 정답시도 indicator 한 변은
  `min(window width, window height) × 0.090`입니다. 몸으로말해요에서는 세로가
  화면 높이의 50%인 green indicator와 중앙 하늘색 구분선 사이에 배치됩니다.
- 정답시도의 진입 side, 정답, 오답, 취소는 게임별 고유 TTL을 사용합니다.
- TTL code `12`, `22`, `50`, `61`은 PsychoPy 내장 `AudioClip.square()`로 생성한
  440 Hz 구형파(0.1초)의 onset을 해당 Display 0 flip의 TTL latch HIGH와 같은
  callback에 묶습니다. code `61`은 Nonverbal Control 확인에서 `예`를 선택해
  본 Control을 시작하는 event입니다.
- PsychoPy가 첫 HDMI 출력 장치를 임의 선택하지 않도록 모든 task sound의 출력은
  `스피커(Realtek(R) Audio)`에 명시적으로 고정합니다. 시작 로그의 `[SOUND]`
  행에 실제 장치 이름과 PTB index를 기록합니다.
- 정답시도 화면에서 좌우 방향키로 `정답시도취소`를 선택한 뒤 Enter를 누르면 해당 시도를 취소하고 원래 게임 화면으로 복귀합니다.

## 연결 테스트

본 task 실행 전에 사용할 수 있도록 시험용 Python 스크립트를 `tests/` 폴더에
별도로 마련했습니다. 프로젝트 루트에서 아래와 같이 module 방식으로 실행해야
`task` package import 경로가 일관되게 유지됩니다.

Display 0/1/2의 물리 화면 매핑 확인:

```powershell
python -m tests.display_test
```

TTL이 Natus Quantum에 정상 표시되는지 확인:

```powershell
python -m tests.connection_test
```

`T` 입력 → decimal 85 (bitmask `01010101`) 전송, `ESC` 종료.

이 시험은 PC–LabJack–Natus 사이의 기본 연결과 code 85 수신 여부를 확인합니다.
실제 `main.py`의 flip callback, 전체 task Event Code, 화면·sound 동기화까지 보장하는
통합 시험은 아닙니다. 최종 실험 전에는 Natus recording 상태에서 `main.py`의
대표 code와 TXT의 `[TTL]` 행을 직접 대조해야 합니다.

`T`를 눌러 latch가 상승하면 connection test도
`[TTL] ... | code= 85 | connection_test` 행을 terminal과 새
`task_done_*.txt`에 함께 기록합니다.

Wisecoco 네 가지 in-game 상태의 검수 PNG 생성:

```powershell
python -m tests.render_wisecoco_previews
```

## 화면 해상도와 반응형 배치

물리 화면 번호는 `task/config.py`의 Display index를 사용합니다.

```python
DISPLAY_0_INDEX = 0
DISPLAY_1_INDEX = 1
DISPLAY_2_INDEX = 2

DISPLAY_0_SIZE = (1440, 900)
DISPLAY_1_SIZE = (1920, 1080)
DISPLAY_2_SIZE = (1920, 1080)
```

실물 fullscreen 실행 시 Window 크기는 위 `DISPLAY_*_SIZE`에 고정되지 않습니다.
Windows/pyglet이 각 monitor에 대해 보고한 현재 native width와 height를 자동으로
사용합니다. `DISPLAY_*_SIZE`는 role별 기준 종횡비와 mock-up fallback 값입니다.

Wisecoco 두 대는 Windows에서 권장 사양인 1920×1080, 120Hz로 먼저 설정합니다.
실제 물리 배치와 출력이 다르면 `DISPLAY_*_INDEX`를 조정하고
`python -m tests.display_test`로 다시 확인합니다. 다른 해상도·종횡비의 monitor도
반응형 배치를 사용하지만, 서로 다른 refresh rate의 광학 onset 동기성은 별도
계측이 필요합니다.

공통 renderer는 실제 `win.size`, text 위치에서 가장자리까지의 safe area, UI별
최대 width/height와 PsychoPy font bounding box를 사용합니다. 이름·제시어·파일명이
길면 영역 안에 들어올 때까지 font height를 자동으로 낮춥니다. mock-up에서는
노트북 화면을 가로 3개 slot으로 나누고 Display 0은 노트북 종횡비, Display 1/2는
Wisecoco 기준 종횡비를 유지합니다.

긴 이름과 단어를 포함한 `480×270`, `800×600`, `1000×300` Window 검사를
통과했지만, 이는 software layout 검증입니다. 실제 장비 배치와 fullscreen 출력은
반드시 `python -m tests.display_test`로 확인하십시오.

## 화면·Sound·TTL 동기화

`GameState`가 반환한 `TriggerEvent`는 `DisplayRouter.present()`에서 한 번만
처리됩니다. 해당 frame에는 Display 0 최좌하단 photodiode marker를 먼저 그리고,
TTL data bit를 설정한 뒤 **Display 0의 같은 flip callback**에서 latch를 올립니다.
몸으로말해요 자동 전환이면 같은 callback에서 sound 재생도 요청합니다.

```text
TriggerEvent 발생
→ Display 0 backbuffer에 photodiode marker draw
→ TTL data bits 설정
→ setup 2 ms
→ Display 1 flip
→ Display 2 flip
→ Display 0 flip:
   photodiode marker 송출 + latch high (+ 필요 시 sound.play)
→ latch high 총 20 ms 유지
→ latch low
→ hold 2 ms
→ data bits clear
```

### Display 0 photodiode marker

- 색상: PsychoPy `rgb=[1, 1, 1]`, 일반 RGB 기준 `(255, 255, 255)` pure white
- 형태: 정사각형
- 크기: Display 0 green/red indicator와 동일하게
  `min(window width, window height) × 0.090`
- 위치: 현재 Display 0 Window의 최좌하단
- 지속시간: trigger가 발생한 첫 frame을 포함하여 정확히 Display 0 flip 4회
- 120Hz에서 frame drop이 없다면 nominal 표시시간은
  `4 × 8.333... ms = 약 33.333 ms`

marker는 다른 Display 0 UI를 모두 그린 뒤 마지막에 추가되므로 항상 최상단에
표시됩니다. 다중 물리 display 모드는 OS가 보고한 native 크기의 fullscreen을
강제하며, marker는 fullscreen Display 0의 최좌하단에 놓입니다. mock-up 3분할에서는
실제 TTL은 전송되지 않지만 동일한 논리 `TriggerEvent`에 반응하여 축소된
`DISPLAY 0 | operator` Window의 최좌하단에서 똑같이 4 frame 표시됩니다.

### 세 사건의 시간 관계

현재 flip 순서는 Display 1 → Display 2 → Display 0입니다. 세 display가 모두
120Hz이고 frame drop이 없다는 가정에서 한 refresh period는 약 `8.333 ms`입니다.

| 사건 간 거리 | 코드상 관계 | 120Hz nominal 범위 |
|---|---|---:|
| Display 1 화면 → Display 2 화면 | 순차 flip | 약 `0–8.333 ms` |
| Display 2 화면 → Display 0 popup/marker | 순차 flip | 약 `0–8.333 ms` |
| Display 1 화면 → Display 0 popup/marker | 두 번의 순차 flip | 약 `0–16.667 ms` |
| Display 0 popup → photodiode marker | 같은 backbuffer와 같은 flip | `0 frame` |
| Display 0 flip → TTL latch HIGH 요청 | 같은 flip callback | software상 거의 직후 |

위 범위는 monitor VBlank phase가 독립적일 때의 nominal 설명이며 고정 보장값이
아닙니다. refresh rate가 서로 다르거나 Windows compositor/GPU buffering 또는
frame drop이 발생하면 더 길어질 수 있습니다.

위 `2/20/2 ms`는 software 설정값입니다. TTL callback과 marker draw는 하나의
`TriggerEvent`와 동일한 Display 0 flip에 결합되어 있지만, photodiode가 감지하는
실제 광학 onset에는 panel scanout·pixel response가 포함됩니다. 또한 서로 다른
물리 monitor의 VBlank phase, audio buffer 및 입력 장치 지연은 코드만으로 정확한
ms 값을 확정할 수 없습니다. 최종 실험 전 photodiode·audio loopback·TTL을 함께
기록하여 실제 offset과 jitter를 측정해야 합니다.

## 로그

실행 로그는 `task_done_texts/task_done_<일시>.txt`에 저장됩니다 (터미널 출력과 동일 내용, utf-8-sig).

```text
[TTL] 21:15:38.427 | code= 12 | Enter / NameGame 본게임 시작 | 왼쪽(철수) 단어: 우산 | 오른쪽(영희) 단어: 계단
[TTL] 21:15:40.594 | code= 23 | Enter/터치: body 오른쪽(영희) 정답시도
[TTL] 21:15:44.103 | code= 25 | 정답맞음(body) -> 차례유지 | 왼쪽(철수) 단어: 수건
[TTL] 21:15:48.550 | code= 43 | P / body_game right PASS | 오른쪽(영희) 단어: 연필 (2/17)
[TTL] 21:16:02.311 | code= 50 | Enter / Verbal Control 시작 | i=1
[TTL] 21:16:05.906 | code= 52 | Space / Verbal Control 다음 문장 | i=2
[TTL] 21:16:08.127 | code= 53 | Backspace / Verbal Control 이전 문장 | i=1
```

- `main.py`에서 `TriggerEvent`가 발생하면 실제 TTL latch 상승 callback이
  `[TTL] 시각 | code | 설명` 한 행을 출력합니다. 같은 stdout은
  `TerminalLogSession`이 terminal과 현재 TXT 양쪽에 즉시 기록하므로 모든
  task TTL 전송은 해당 실행의 log TXT에 남습니다.
- 게임 시작 TTL에는 좌·우 최초 제시어를 각각
  `왼쪽(이름) 단어: 첫 단어` 형식으로 기록합니다.
- 정답 또는 PASS로 제시어가 진행되면 해당 TTL 행에 실제 변경된 side를
  `왼쪽/오른쪽(이름) 단어: 새 단어` 형식으로 기록합니다.
- VC 시작과 모든 Space/Backspace event는 결과 문장 번호를 동일 TTL 행 끝에
  1-based `i=<번호>` 형식으로 기록합니다. 첫 문장의 Backspace와 마지막 문장의
  종료 Space도 각각 현재 index인 `i=1`, `i=10`을 기록합니다.
- 게임 중에는 `[TTL]` 행만 이벤트 로그로 기록하며 `[TOUCH]`, `[TURN]`,
  `[WORD]`, `[WORD LIST]` 행은 기록하지 않습니다.

git에는 폴더 구조만 유지되며 실제 `.txt` 로그는 업로드되지 않습니다.
