"""Wisecoco 네 게임 상태의 1920x1080 검수 PNG를 생성한다."""

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from task.config import GRAY, GREEN, SKY_BLUE, WHITE, WISECOCO_MAIN_AREA_RATIO
from task.words import WORD_LIST


def _find_output_dir() -> Path:
    """현재 Windows 로캘과 무관하게 사용자가 만든 codex 폴더를 찾는다."""
    override = os.environ.get("WISECOCO_PREVIEW_DIR")
    if override:
        return Path(override)
    matches = [path for path in PROJECT_DIR.glob("codex*") if path.is_dir()]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one codex* directory, found: {matches}")
    return matches[0]
SIZE = (1920, 1080)
WORD = WORD_LIST[0]


def _rgb(color: list[float]) -> tuple[int, int, int]:
    return tuple(round((channel + 1.0) * 127.5) for channel in color)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", size=size)


def _centered(draw: ImageDraw.ImageDraw, xy, text: str, font, width: int) -> None:
    draw.multiline_text(
        xy, text, fill=_rgb(WHITE), font=font, anchor="mm",
        align="center", spacing=12,
    )


def render(*, verbal: bool, activation: bool, progress: float = 0.0) -> Image.Image:
    width, height = SIZE
    boundary = round(width * WISECOCO_MAIN_AREA_RATIO)
    main_center = boundary // 2
    action_center = boundary + (width - boundary) // 2
    image = Image.new("RGB", SIZE, _rgb(GRAY))
    draw = ImageDraw.Draw(image)

    if activation and verbal:
        draw.rectangle((0, 0, boundary, height), fill=_rgb(GREEN))
    elif activation and not verbal:
        green_top = round(height * max(0.0, min(1.0, progress)))
        draw.rectangle((0, green_top, boundary, height), fill=_rgb(GREEN))

    draw.line((boundary, 0, boundary, height), fill=_rgb(SKY_BLUE), width=5)
    _centered(draw, (main_center, height // 2), WORD, _font(59), boundary)

    if activation and verbal:
        draw.line((boundary, height // 2, width, height // 2), fill=_rgb(SKY_BLUE), width=5)
        _centered(draw, (action_center, height // 4), "차례넘기기\n(터치)", _font(54), width - boundary)
        _centered(draw, (action_center, height * 3 // 4), "정답시도\n(터치)", _font(54), width - boundary)
    elif activation:
        _centered(draw, (action_center, height // 2), "정답시도\n(터치)", _font(54), width - boundary)
    elif verbal:
        _centered(draw, (action_center, height // 2), "상대가 차례를 넘길\n때까지 기다리세요", _font(44), width - boundary)
    else:
        _centered(draw, (action_center, height // 2), "상대의 차례가 끝날\n때까지 기다리세요", _font(44), width - boundary)
    return image


def main() -> None:
    output_dir = _find_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    previews = {
        "Verbal_Activation_Positive.png": render(verbal=True, activation=True),
        "Verbal_Activation_Negative.png": render(verbal=True, activation=False),
        "Nonverbal_Activation_Positive.png": render(verbal=False, activation=True, progress=0.38),
        "Nonverbal_Activation_Negative.png": render(verbal=False, activation=False),
    }
    for filename, image in previews.items():
        path = output_dir / filename
        image.save(path)
        print(path)


if __name__ == "__main__":
    main()
