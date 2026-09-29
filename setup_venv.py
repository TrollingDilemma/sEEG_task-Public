import os
import sys
import subprocess
from pathlib import Path

VENV_DIR = ".venv"

REQUIRED_MAJOR = 3
REQUIRED_MINOR = 10
PSYCHOPY_VERSION = "2026.1.3"


def run_command(command, description=None):
    if description:
        print(f"\n[진행] {description}")

    print("실행 명령:", " ".join(command))

    result = subprocess.run(command)

    if result.returncode != 0:
        print(f"\n[오류] 명령실행실패: {' '.join(command)}")
        sys.exit(result.returncode)


def run_command_capture(command):
    """명령의 stdout을 반환하고 실패하면 None을 반환한다."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def find_python310():
    """Windows py launcher에서 Python 3.10 실행 파일을 찾는다."""
    if os.name != "nt":
        print("[오류] 이 스크립트는 현재 Windows 기준으로 작성되어 있습니다.")
        sys.exit(1)

    python310_path = run_command_capture(
        [
            "py",
            "-3.10",
            "-c",
            "import sys; print(sys.executable)"
        ]
    )

    if python310_path is None or python310_path == "":
        print("\n[오류] Python 3.10을 찾을 수 없습니다.")
        print("먼저 Python 3.10 64-bit를 설치해야 합니다.")
        print("설치 후 아래 명령으로 확인하십시오:")
        print("  py -3.10 --version")
        sys.exit(1)

    print(f"[확인] Python 3.10 경로: {python310_path}")
    return python310_path


def get_venv_python_path():
    base = Path(VENV_DIR)

    if os.name == "nt":
        return base / "Scripts" / "python.exe"
    else:
        return base / "bin" / "python"


def check_venv_python_version(venv_python):
    """가상환경의 major/minor version을 검증한다."""
    version_text = run_command_capture(
        [
            str(venv_python),
            "-c",
            "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        ]
    )

    if version_text != f"{REQUIRED_MAJOR}.{REQUIRED_MINOR}":
        print(f"\n[오류] 현재 .venv Python 버전: {version_text}")
        print(f"필요한 버전: {REQUIRED_MAJOR}.{REQUIRED_MINOR}")
        print("\n기존 .venv를 삭제한 뒤 다시 실행하십시오:")
        print("  rmdir /s /q .venv")
        print("  python setup_venv.py")
        sys.exit(1)

    print(f"[확인] .venv Python 버전: {version_text}")


def create_venv():
    """Python 3.10으로 가상환경을 생성한다."""
    if Path(VENV_DIR).exists():
        print(f"\n[확인] {VENV_DIR} 가상환경이 이미 존재합니다. 새로 만들지 않습니다.")
        return

    python310_path = find_python310()

    run_command(
        [
            python310_path,
            "-m",
            "venv",
            VENV_DIR
        ],
        description=f"Python 3.10 기반 {VENV_DIR} 가상환경 생성"
    )


def upgrade_pip(venv_python):
    run_command(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "pip==23.3.2",
            "setuptools==68.2.2",
            "wheel==0.41.3"
        ],
        description="pip, setuptools, wheel 버전 고정"
    )


def install_labjack(venv_python):
    run_command(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "labjack-ljm"
        ],
        description="LabJack Python package 설치"
    )

def install_esprima_legacy(venv_python):
    run_command(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "--no-build-isolation",
            "--no-use-pep517",
            "esprima==4.0.1"
        ],
        description="esprima legacy 방식 선설치"
    )

def install_psychopy(venv_python):
    run_command(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            f"psychopy=={PSYCHOPY_VERSION}"
        ],
        description=f"PsychoPy {PSYCHOPY_VERSION} 설치"
    )


def test_imports(venv_python):
    test_code = """
from labjack import ljm
import psychopy

print("LabJack import OK")
print("PsychoPy import OK")
"""

    run_command(
        [
            str(venv_python),
            "-c",
            test_code
        ],
        description="import test"
    )


def main():
    print("====================================")
    print("Natus trigger project 가상환경 설치")
    print("====================================")

    create_venv()

    venv_python = get_venv_python_path()

    if not venv_python.exists():
        print(f"\n[오류] 가상환경 Python을 찾을 수 없습니다: {venv_python}")
        sys.exit(1)

    check_venv_python_version(venv_python)

    upgrade_pip(venv_python)
    install_labjack(venv_python)
    install_esprima_legacy(venv_python)
    install_psychopy(venv_python)
    test_imports(venv_python)

    print("\n[완료] Python 3.10 기반 가상환경 설치가 완료되었습니다.")


if __name__ == "__main__":
    main()
