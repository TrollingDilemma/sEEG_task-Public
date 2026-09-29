"""Display 0 word-list keyboard grid의 배치를 계산한다."""

from math import ceil


MAX_GRID_COLUMNS = 4


def grid_shape(option_count: int) -> tuple[int, int]:
    """목록 수에 맞는 (행, 최대 열) 수를 반환한다."""
    if option_count <= 0:
        raise ValueError("Word-list grid requires at least one option.")
    columns = min(MAX_GRID_COLUMNS, option_count)
    rows = ceil(option_count / MAX_GRID_COLUMNS)
    return rows, columns


def row_indices(row: int, option_count: int) -> range:
    """주어진 행에 들어가는 option index 범위를 반환한다."""
    start = row * MAX_GRID_COLUMNS
    stop = min(start + MAX_GRID_COLUMNS, option_count)
    return range(start, stop)
