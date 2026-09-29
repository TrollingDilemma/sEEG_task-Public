"""선택된 txt 단어 목록을 불러오고 무작위 제시 순서를 관리한다."""

import random
from collections.abc import Iterator
from pathlib import Path

from .config import (
    WORD_LIST_FILE_PREFIX,
    WORD_LIST_FILE_SUFFIX,
    WORD_LIST_SET,
    WORD_LISTS_DIR,
)


def get_word_list_path(list_name: str) -> Path:
    """list 이름을 대응하는 txt 파일 경로로 변환한다."""
    normalized_name = (list_name or "").strip()
    if not normalized_name:
        raise ValueError("Word-list name must not be empty.")
    if Path(normalized_name).name != normalized_name:
        raise ValueError(f"Invalid word-list name: {list_name!r}")
    return (
        WORD_LISTS_DIR
        / f"{WORD_LIST_FILE_PREFIX}{normalized_name}{WORD_LIST_FILE_SUFFIX}"
    )


def load_word_list(list_name: str = WORD_LIST_SET) -> list[str]:
    """txt에서 단어를 읽고 개수·공백·중복을 검증한다."""
    path = get_word_list_path(list_name)
    if not path.is_file():
        raise FileNotFoundError(
            f"Word-list file not found for WORD_LIST_SET={list_name!r}: {path}"
        )

    words = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()]
    words = [word for word in words if word]
    if not words:
        raise ValueError(
            f"{path.name} must contain at least one non-empty word."
        )
    duplicate_words = sorted({word for word in words if words.count(word) > 1})
    if duplicate_words:
        raise ValueError(f"Duplicate words in {path.name}: {duplicate_words}")
    return words


def list_available_word_lists() -> list[str]:
    """선택 가능한 파일을 검색하고 모든 목록의 형식을 실행 전에 검증한다."""
    pattern = f"{WORD_LIST_FILE_PREFIX}*{WORD_LIST_FILE_SUFFIX}"
    names = []
    for path in WORD_LISTS_DIR.glob(pattern):
        filename = path.name
        name = filename[
            len(WORD_LIST_FILE_PREFIX):-len(WORD_LIST_FILE_SUFFIX)
        ]
        if name:
            names.append(name)
    names = sorted(set(names), key=str.casefold)
    if not names:
        raise FileNotFoundError(
            f"No word-list files matching {pattern!r} in {WORD_LISTS_DIR}"
        )
    for name in names:
        load_word_list(name)
    return names


# list_name을 생략하는 호환 경로에서 사용하는 기본 목록.
WORD_LIST = tuple(load_word_list())


def iter_randomized_words(
    rng: random.Random | None = None,
    *,
    list_name: str | None = None,
) -> Iterator[str]:
    """목록의 모든 단어를 무작위 순열로 만들어 중복 없이 하나씩 반환한다.

    원본 ``WORD_LIST``의 순서는 변경하지 않는다. 테스트에서 같은 순서를
    재현해야 할 때는 ``random.Random(seed)`` 객체를 ``rng``에 전달한다.
    """
    source_words = load_word_list(list_name) if list_name is not None else WORD_LIST
    shuffled_words = list(source_words)
    (rng or random).shuffle(shuffled_words)
    yield from shuffled_words
