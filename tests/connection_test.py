import time
from datetime import datetime

from labjack import ljm
from psychopy import visual, core
from psychopy.hardware import keyboard

from task.logger import TerminalLogSession, get_next_task_done_log_path
from task.ttl import format_trigger_timestamp

TRIGGER_CODE = 0b01010101
LATCH_DURATION_SEC = 0.020

DATA_LINES = ["EIO0", "EIO1", "EIO2", "EIO3", "EIO4", "EIO5", "EIO6", "EIO7"]
LATCH_LINE = "CIO0"

def initialize_outputs(handle):
    for line in DATA_LINES + [LATCH_LINE]:
        ljm.eWriteName(handle, line, 0)

def write_data_lines(handle, code):
    for bit_index, line in enumerate(DATA_LINES):
        bit_value = (code >> bit_index) & 1
        ljm.eWriteName(handle, line, bit_value)

def clear_data_lines(handle):
    for line in DATA_LINES:
        ljm.eWriteName(handle, line, 0)

def send_trigger(handle, code):
    write_data_lines(handle, code)

    time.sleep(0.005)

    ljm.eWriteName(handle, LATCH_LINE, 1)
    timestamp = format_trigger_timestamp(datetime.now())
    print(f"[TTL] {timestamp} | code={code:3d} | connection_test")
    time.sleep(LATCH_DURATION_SEC)
    ljm.eWriteName(handle, LATCH_LINE, 0)

    time.sleep(0.005)
    clear_data_lines(handle)

def run_connection_test():
    handle = None
    win = None

    try:
        handle = ljm.openS("T4", "ANY", "ANY")
        print("LabJackT4 연결됨")

        initialize_outputs(handle)
        clear_data_lines(handle)
        ljm.eWriteName(handle, LATCH_LINE, 0)

        win = visual.Window(size = [900, 500], color = "gray", units = "pix", fullscr = False)
        text = visual.TextStim(
            win,
            text = (
                "PC -> NatusQuantum Trigger Test\n\n"
                "Press T to send test TTL\n"
                "decimal code = 85 | bitmask = 01010101\n\n"
                "ESC -> Quit"
                ),
            color = "white",
            height = 32,
            alignText = "center",
            pos = (0,0)
            )
        kb = keyboard.Keyboard()
        kb.clearEvents()

        text.draw()
        win.flip()

        while True:
            keys = kb.getKeys(keyList = ["t", "escape"], clear = True)
            for key in keys:
                if key.name == "t":
                    send_trigger(handle, TRIGGER_CODE)
                    core.wait(0.2)
                    kb.clearEvents()
                elif key.name == "escape":
                    print("Quit")
                    return
            core.wait(0.01)
        
    except Exception as e:
        print("Error occured: ")
        print(e)

    finally:
        if handle is not None:
            try:
                clear_data_lines(handle)
                ljm.eWriteName(handle, LATCH_LINE, 0)
                ljm.close(handle)
                print("LabJackT4 연결 종료")
             
            except Exception:
                pass

        if win is not None:
            try:
                win.close()
            except Exception:
                pass

        core.quit()

def main():
    created_at = datetime.now()
    log_path = get_next_task_done_log_path(created_at)
    with TerminalLogSession(log_path, created_at):
        run_connection_test()


if __name__ == "__main__":
    main()

        
