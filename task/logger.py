import sys
from pathlib import Path
from datetime import datetime

from .config import (
    LOG_TIMESTAMP_FOR_FILENAME_FORMAT,
    LOG_TIMESTAMP_FOR_TEXT_FORMAT,
    TASK_DONE_FILE_PREFIX,
    TASK_DONE_FILE_SUFFIX,
    TASK_DONE_TEXTS_DIR,
)


class TeeStream:
    """출력을 terminal과 session log에 동시에 기록한다."""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data: str):
        for stream in self.streams:
            stream.write(data)
            stream.flush()
        return len(data)

    def flush(self):
        for stream in self.streams:
            stream.flush()

    def isatty(self):
        return False

def get_next_task_done_log_path(created_at: datetime) -> Path:
    """동일 timestamp 파일과 충돌하지 않는 session log 경로를 반환한다."""
    TASK_DONE_TEXTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp_for_filename = created_at.strftime(LOG_TIMESTAMP_FOR_FILENAME_FORMAT)

    base_log_path = (
        TASK_DONE_TEXTS_DIR
        / f"{TASK_DONE_FILE_PREFIX}{timestamp_for_filename}{TASK_DONE_FILE_SUFFIX}"
    )

    if not base_log_path.exists():
        return base_log_path

    index = 1
    while True:
        log_path = (
            TASK_DONE_TEXTS_DIR
            / f"{TASK_DONE_FILE_PREFIX}{timestamp_for_filename}_{index}{TASK_DONE_FILE_SUFFIX}"
        )

        if not log_path.exists():
            return log_path

        index += 1

class TerminalLogSession:
    """context 내부 stdout/stderr를 terminal과 UTF-8 log에 기록한다."""
    def __init__(self, log_path: Path, created_at: datetime):
        self.log_path = log_path
        self.created_at = created_at
        self.created_at_text = created_at.strftime(LOG_TIMESTAMP_FOR_TEXT_FORMAT)

        self.log_file = None
        self.original_stdout = None
        self.original_stderr = None

    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # utf-8-sig: Windows 메모장에서 한글이 깨질 가능성을 줄이기 위함
        self.log_file = open(
            self.log_path,
            mode="w",
            encoding="utf-8-sig",
            buffering=1,
        )

        sys.stdout = TeeStream(self.original_stdout, self.log_file)
        sys.stderr = TeeStream(self.original_stderr, self.log_file)

        print(f"작성일시: {self.created_at_text}")
        print("====================================")
        print("[LOG] Terminal log 저장 시작")
        print(f"[LOG] 저장 파일: {self.log_path}")
        print("====================================")

        return self.log_path

    def __exit__(self, exc_type, exc_value, exc_traceback):
        finished_at = datetime.now()
        finished_at_text = finished_at.strftime(LOG_TIMESTAMP_FOR_TEXT_FORMAT)

        print("\n====================================")
        print("[LOG] Terminal log 저장 종료")
        print(f"종료일시: {finished_at_text}")
        print(f"[LOG] 저장 파일: {self.log_path}")
        print("====================================")

        try:
            sys.stdout.flush()
            sys.stderr.flush()
        finally:
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr

            if self.log_file is not None:
                self.log_file.close()

        return False
