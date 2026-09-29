import traceback
from datetime import datetime

from task.app import run_task
from task.logger import TerminalLogSession, get_next_task_done_log_path


def main() -> None:
    log_created_at = datetime.now()
    log_path = get_next_task_done_log_path(log_created_at)

    with TerminalLogSession(log_path, log_created_at):
        try:
            run_task()
        except Exception:
            print("\n[ERROR] main.py 실행 중 예외 발생")
            print("[ERROR] Traceback:")
            traceback.print_exc()
            raise


if __name__ == "__main__":
    main()