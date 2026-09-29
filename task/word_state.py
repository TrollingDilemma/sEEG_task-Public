"""좌·우 독립 word permutation과 현재 index를 관리한다."""

from dataclasses import dataclass, field

from .config import WORD_LIST_SET
from .words import iter_randomized_words, load_word_list


@dataclass
class WordState:
    list_name: str = WORD_LIST_SET
    arrays: dict[str, list[str]] = field(default_factory=dict)
    indices: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.regenerate()

    def regenerate(self) -> None:
        """새 game session에 사용할 좌·우 독립 permutation을 만든다."""
        self.arrays = {
            "left": list(iter_randomized_words(list_name=self.list_name)),
            "right": list(iter_randomized_words(list_name=self.list_name)),
        }
        self.indices = {"left": 0, "right": 0}

        # 두 permutation의 첫 단어가 같으면 게임 시작부터 충돌한다. 오른쪽
        # permutation 안에서 첫 단어만 교환해 각 행의 무작위 순열 성질은
        # 유지하면서 초기 표시 단어를 다르게 만든다.
        if len(self.arrays["right"]) > 1 and self.current("left") == self.current("right"):
            self.arrays["right"][0], self.arrays["right"][1] = (
                self.arrays["right"][1],
                self.arrays["right"][0],
            )

    def select(self, list_name: str) -> None:
        """선택 목록을 바꾸고 좌·우 permutation을 새로 만든다."""
        load_word_list(list_name)
        self.list_name = list_name
        self.regenerate()

    def current(self, side: str) -> str:
        return self.arrays[side][self.indices[side]]

    def skip_on_conflict(self, side: str, next_index: int) -> int:
        """상대 행의 현재 단어와 충돌할 한 칸을 건너뛴 index를 반환한다.

        건너뛰기는 중간 단어를 표시하지 않는 원자적인 2칸 점프다. 단어가
        하나뿐이면 충돌을 피할 다른 위치가 없으므로 원래 index를 반환한다.
        """
        if len(self.arrays[side]) == 1:
            return next_index

        other_side = "right" if side == "left" else "left"
        if self.arrays[side][next_index] == self.current(other_side):
            return (next_index + 1) % len(self.arrays[side])
        return next_index

    def proceed(self, side: str) -> tuple[str, str, int]:
        """다음 단어로 이동하되 상대 행과 충돌하면 한 단어를 건너뛴다."""
        previous_word = self.current(side)
        next_index = (self.indices[side] + 1) % len(self.arrays[side])
        next_index = self.skip_on_conflict(side, next_index)
        self.indices[side] = next_index
        next_word = self.current(side)
        return previous_word, next_word, next_index
