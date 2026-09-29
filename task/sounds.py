from pathlib import Path
from psychopy import sound
from psychopy.hardware.speaker import SpeakerDevice
from psychopy.sound.audioclip import AudioClip

from .config import (
    AUDIO_OUTPUT_DEVICE_NAME,
    STATE_TRANSITION_TONE_DURATION_SEC,
    STATE_TRANSITION_TONE_GAIN,
    STATE_TRANSITION_TONE_HZ,
)


_output_speaker = None


def get_output_speaker() -> SpeakerDevice:
    """Task sound가 HDMI가 아닌 노트북 Realtek speaker를 공유하게 한다."""
    global _output_speaker
    if _output_speaker is None:
        _output_speaker = SpeakerDevice(name=AUDIO_OUTPUT_DEVICE_NAME)
        print(
            "[SOUND] 출력 장치 | "
            f"name={_output_speaker.name} | index={_output_speaker.index}"
        )
    return _output_speaker


def load_sound_effect(path: Path, label: str):
    """실행 전에 sound를 load하여 경로 오류를 조기에 검출한다."""
    if not path.exists():
        raise FileNotFoundError(f"[SOUND ERROR] {label} sound file not found: {path}")
    return sound.Sound(value=str(path), speaker=get_output_speaker())


def create_state_transition_tone():
    """PsychoPy 내장 AudioClip으로 440 Hz, 0.7 s 구형파를 생성한다."""
    clip = AudioClip.square(
        duration=STATE_TRANSITION_TONE_DURATION_SEC,
        freqHz=STATE_TRANSITION_TONE_HZ,
        dutyCycle=0.5,
        gain=STATE_TRANSITION_TONE_GAIN,
    )
    return sound.Sound(value=clip, speaker=get_output_speaker())
