# TTL Event Codebook — Control + NameGame + 몸으로말해요

sEEG task의 LabJack 8-bit TTL event code 단일 기준 문서입니다. Control,
NameGame, 몸으로말해요의 전이와 실제 TTL/log 의미를 정의합니다.

## 원칙

- 각 code는 게임과 주요 state transition을 고유하게 구분한다.
- 시작 side, 정답시도자, 차례 전환, PASS처럼 좌·우 구분이 필요한 event는
  side를 code에 직접 인코딩한다.
- 선택 이동(←/→)에는 trigger가 없다.
- word-list 방향키 이동과 Enter 확정에는 별도 trigger가 없다.
- 시작 전 touch mode 선택값 1/2와 Windows 설정 macro에는 trigger가 없다.
- Verbal Control 진행 event는 50번대, Nonverbal Control 세부 event는
  60번대를 사용한다.
- 종료 확인 화면은 Enter 확정 결과에 따라 6, 7, 34를 보낸다.
- 아래 모든 TTL Event Code는 동일 event frame의 Display 0 flip에서 latch를
  올리고 4-frame pure-white photodiode marker를 시작한다.
- code 12, 22, 50, 61은 같은 flip callback에서 PsychoPy 내장 기능으로 생성한
  440 Hz 구형파(0.7초) 재생도 시작한다.
- `0`은 data line clear 상태로 예약한다.

## 범위 구조

| 범위 | 카테고리 |
|---|---|
| 01-07 | 시스템 / 게임 선택 / 종료 (code 4는 legacy 예약) |
| 10-19 | NameGame (십의자리 1) |
| 20-29 | 몸으로말해요 (십의자리 2) |
| 30-34 | 재설정 / 선택 화면 복귀 (십의자리 3) |
| 40-44 | Control 확인 / PASS (십의자리 4) |
| 50-56 | Verbal Control (십의자리 5) |
| 57-59 | Verbal Control 후속 event 예약 |
| 60-65 | Nonverbal Control (십의자리 6) |
| 66-69 | Nonverbal Control 후속 event 예약 |

VC 확인 진입은 code 40을 사용하고 PASS는 바로 뒤의 41–44에 연속
배치합니다. NVC의 확인·시작·취소·종료·복귀는 60–65에 순서대로 배치합니다.

## Code Table

| code | 상수명 | 발생 지점 -> 행선지 |
|---|---|---|
| **시스템** ||
| 1 | `CODE_SELECT_GAME_ENTER` | 세션 시작 -> select_game |
| 2 | `CODE_SELECT_NAMEGAME` | select_game Enter -> name_order |
| 3 | `CODE_SELECT_BODYGAME` | select_game Enter -> body_order |
| 4 | — | legacy Nonverbal Control 직접 진입 code(신규 event 송출 없음) |
| 5 | `CODE_EXIT_REQUEST` | Ctrl+Q -> exit_confirm |
| 6 | `CODE_EXIT_YES` | exit_confirm `예` Enter -> 프로그램 종료 |
| 7 | `CODE_EXIT_NO` | exit_confirm `아니오` Enter -> 직전 state 복귀 |
| **NameGame** ||
| 10 | `CODE_NAME_FIRST_RIGHT` | name_order Enter -> 오른쪽 먼저 / name_word_list |
| 11 | `CODE_NAME_FIRST_LEFT` | name_order Enter -> 왼쪽 먼저 / name_word_list |
| 12 | `CODE_NAME_GAME_START` | name_start_confirm Enter -> name_game |
| 13 | `CODE_NAME_TRY_RIGHT` | Enter/터치: name 오른쪽 activated side 정답시도 -> try_answering |
| 14 | `CODE_NAME_TRY_LEFT` | Enter/터치: name 왼쪽 activated side 정답시도 -> try_answering |
| 15 | `CODE_NAME_TRY_YES` | name 정답 -> name_game 복귀 |
| 16 | `CODE_NAME_TRY_NO` | name 오답 -> name_game 복귀 |
| 17 | `CODE_NAME_TRY_CANCEL` | name 정답시도취소 선택 후 Enter -> name_game 복귀 |
| 18 | `CODE_NAME_TURN_TO_RIGHT` | Space/터치: name_game -> 오른쪽 차례 |
| 19 | `CODE_NAME_TURN_TO_LEFT` | Space/터치: name_game -> 왼쪽 차례 |
| **몸으로말해요** ||
| 20 | `CODE_BODY_FIRST_RIGHT` | body_order Enter -> 오른쪽 먼저 / body_word_list |
| 21 | `CODE_BODY_FIRST_LEFT` | body_order Enter -> 왼쪽 먼저 / body_word_list |
| 22 | `CODE_BODY_GAME_START` | body_start_confirm Enter -> body_game |
| 23 | `CODE_BODY_TRY_RIGHT` | Enter/터치: body 오른쪽 activated side 정답시도 -> try_answering |
| 24 | `CODE_BODY_TRY_LEFT` | Enter/터치: body 왼쪽 activated side 정답시도 -> try_answering |
| 25 | `CODE_BODY_TRY_YES` | body 정답 -> body_game 복귀 |
| 26 | `CODE_BODY_TRY_NO` | body 오답 -> body_game 복귀 |
| 27 | `CODE_BODY_TRY_CANCEL` | body 정답시도취소 선택 후 Enter -> body_game 복귀 |
| 28 | `CODE_BODY_AUTO_TO_RIGHT` | body_game 자동전환 -> 오른쪽 설명 차례 |
| 29 | `CODE_BODY_AUTO_TO_LEFT` | body_game 자동전환 -> 왼쪽 설명 차례 |
| **재설정 / 선택 화면 복귀** ||
| 30 | `CODE_RESET_NAME_ORDER` | name_order R -> select_game |
| 31 | `CODE_RESET_BODY_ORDER` | body_order R -> select_game |
| 32 | `CODE_RESET_NAME_START` | name_word_list/name_start_confirm R -> name_order |
| 33 | `CODE_RESET_BODY_START` | body_word_list/body_start_confirm R -> body_order |
| 34 | `CODE_RESET_EXIT` | exit_confirm `게임 고르기` Enter -> select_game |
| **Control 확인 / PASS** ||
| 40 | `CODE_VERBAL_CONTROL_CONFIRM` | select_game Enter -> verbal_control_confirm |
| 41 | `CODE_NAME_PASS_RIGHT` | host P / NameGame 오른쪽 차례 -> 오른쪽 word 진행 |
| 42 | `CODE_NAME_PASS_LEFT` | host P / NameGame 왼쪽 차례 -> 왼쪽 word 진행 |
| 43 | `CODE_BODY_PASS_RIGHT` | host P / 몸으로말해요 오른쪽 차례 -> 오른쪽 word 진행 |
| 44 | `CODE_BODY_PASS_LEFT` | host P / 몸으로말해요 왼쪽 차례 -> 왼쪽 word 진행 |
| **Verbal Control** ||
| 50 | `CODE_VERBAL_CONTROL_START` | 확인 `예` Enter -> verbal_control / 문장 1 표시 |
| 51 | `CODE_VERBAL_CONTROL_CANCEL` | 확인 `아니오` Enter -> select_game |
| 52 | `CODE_VERBAL_CONTROL_NEXT` | Space -> 다음 문장 표시(i=2–10) |
| 53 | `CODE_VERBAL_CONTROL_PREVIOUS` | Backspace -> 이전 문장 |
| 54 | `CODE_VERBAL_CONTROL_FINISH` | 문장 10에서 Space -> control_finish |
| 55 | `CODE_VERBAL_CONTROL_RETURN` | control_finish `control로 돌아가기` Enter -> verbal_control |
| 56 | `CODE_VERBAL_CONTROL_GAME_SELECT` | control_finish `게임 고르기` Enter -> select_game |
| **Nonverbal Control** ||
| 60 | `CODE_NONVERBAL_CONTROL_CONFIRM` | select_game Enter -> nonverbal_control_confirm |
| 61 | `CODE_NONVERBAL_CONTROL_START` | 확인 `예` Enter -> nonverbal_control |
| 62 | `CODE_NONVERBAL_CONTROL_CANCEL` | 확인 `아니오` Enter -> select_game |
| 63 | `CODE_NONVERBAL_CONTROL_FINISH` | Space -> control_finish |
| 64 | `CODE_NONVERBAL_CONTROL_RETURN` | control_finish `control로 돌아가기` Enter -> nonverbal_control |
| 65 | `CODE_NONVERBAL_CONTROL_GAME_SELECT` | control_finish `게임 고르기` Enter -> select_game |

## 정답시도 흐름

```text
NameGame:
  name_game Enter 또는 activated 화면 정답시도 터치
    -> activated side 정답시도(13=오른쪽 / 14=왼쪽) -> try_answering
  try_answering Y/N 또는 방향키+Enter -> 15/16 -> name_game 복귀, 차례 유지
  host P -> 41(오른쪽 word 진행) / 42(왼쪽 word 진행)

몸으로말해요:
  body_game Enter 또는 activated 화면 정답시도 터치
    -> activated side 정답시도(23=오른쪽 / 24=왼쪽) -> try_answering
  try_answering Y/N 또는 방향키+Enter -> 25/26 -> body_game 복귀, 차례 유지
  host P -> 43(오른쪽 word 진행) / 44(왼쪽 word 진행)

정답시도 취소:
  try_answering 정답시도취소 선택 후 Enter -> 17(name) / 27(body) -> 원래 게임으로 복귀, 차례 유지

word index 진행:
  PASS -> activated(+) side 자신의 word 진행
  정답 -> activated(+) side가 맞힌 상대 side의 word 진행
  Display 1 -> left permutation / Display 2 -> right permutation
  game start TTL -> 좌·우 각각 현재 표시되는 첫 단어
  PASS/정답 TTL -> 변경된 side의 새 단어만 기록
```

## Verbal Control 흐름

```text
select_game에서 Verbal Control Enter -> 40 -> verbal_control_confirm
  예 Enter -> 50 -> verbal_control, Display 1 문장 1 표시
  아니오 Enter -> 51 -> select_game

verbal_control:
  Space -> 52 -> 다음 문장, TTL log에 i 기록
  Backspace -> 53 -> 이전 문장, TTL log에 i 기록
  문장 10에서 Space -> 54 -> control_finish, TTL log에 i=10 기록
  control_finish에서 control 복귀 -> 55
  control_finish에서 게임 고르기 -> 56
```

첫 문장에서 Backspace를 누르면 문장 1을 유지하되 입력 event code 53은
송출합니다. 선택 cursor 이동에는 TTL이 없습니다.

## Nonverbal Control 흐름

```text
select_game에서 Nonverbal Control Enter -> 60 -> nonverbal_control_confirm
  예 Enter -> 61 -> nonverbal_control
  아니오 Enter -> 62 -> select_game
nonverbal_control에서 Space -> 63 -> control_finish
control_finish에서 control 복귀 -> 64
control_finish에서 게임 고르기 -> 65
```

Space를 누른 시점부터 control 종료화면에 머문 시간은 session timer에 포함하지
않습니다. `control로 돌아가기`를 선택하면 NVC 화면과 timer가 이어집니다.

## Photodiode coupling

- 이 표에 정의된 모든 code는 동일한 `TriggerEvent` 경로를 사용한다.
- event 첫 frame의 Display 0 flip callback에서 TTL latch HIGH를 요청한다.
- 같은 Display 0 backbuffer 최좌하단에 pure-white marker를 그리고 총 4 frame
  유지한다.
- code 12, 22, 50, 61에서는 TTL latch HIGH, photodiode marker onset 및
  440 Hz 구형파(0.7초) 재생 요청을 동일한 Display 0 flip에 결합한다.
- mock-up에서는 같은 논리 event와 marker가 발생하지만 LabJack backend가
  실제 TTL을 출력하지 않는다.
- word-list 이동·확정, 선택 cursor 이동, 상단 숫자열 `0` macro처럼 TTL이 없는 입력은
  photodiode marker도 시작하지 않는다.

## TTL 로그 불변 조건

- `main.py` 실행 전체는 `TerminalLogSession` 안에서 이루어진다.
- 모든 `TriggerEvent`는 `DisplayRouter.present()`와
  `FlipSynchronizedTrigger`라는 하나의 경로만 통과한다.
- LabJack latch 상승 callback이 실행된 시점에 `[TTL]` 행을 출력하며, 이 행은
  terminal과 현재 `task_done_*.txt`에 동시에 기록된다.
- 따라서 TTL 전송을 요청한 event에는 하나의 `[TTL]` 행이 대응한다. MOCK-UP은
  실제 전기 신호 없이도 같은 논리 trigger를 `[TTL]` 행으로 기록한다.
- `tests.connection_test`의 test code 85도 latch 상승 시각을 `[TTL]` 행으로
  별도 실행 log TXT에 기록한다. code 85는 본 과제 codebook의 task event가
  아니라 배선 확인 전용이다.
- VC 문장 표시 onset은 `i=1`, 이후 Space/Backspace는 결과 문장 번호를
  1-based `i=<번호>`로 같은 `[TTL]` 행에 기록한다.
