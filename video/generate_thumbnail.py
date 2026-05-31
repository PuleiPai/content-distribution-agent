from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


TEXT_COLOR = "#FFFACD"

PLATFORM_SPECS = {
    "youtube": {"w": 1280, "h": 720, "font_size": 80, "gradient_h": 300, "padding": 60},
    "vertical": {"w": 1080, "h": 1920, "font_size": 72, "gradient_h": 500, "padding": 60},
    "tiktok": {"w": 1080, "h": 1920, "font_size": 72, "gradient_h": 500, "padding": 60},
    "xiaohongshu": {"w": 1080, "h": 1440, "font_size": 72, "gradient_h": 460, "padding": 60},
    "bilibili": {"w": 1280, "h": 720, "font_size": 76, "gradient_h": 300, "padding": 60},
}


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/Library/Fonts/Impact.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_title(draw: ImageDraw.ImageDraw, title: str, font, max_width: int) -> list[str]:
    words = title.split()
    if not words:
        return [""]
    if draw.textlength(title, font=font) <= max_width:
        return [title]

    best_split, best_diff = 1, float("inf")
    for i in range(1, len(words)):
        line1 = " ".join(words[:i])
        line2 = " ".join(words[i:])
        w1 = draw.textlength(line1, font=font)
        w2 = draw.textlength(line2, font=font)
        if w1 <= max_width and w2 <= max_width:
            diff = abs(w1 - w2)
            if diff < best_diff:
                best_diff, best_split = diff, i

    line1 = " ".join(words[:best_split])
    line2 = " ".join(words[best_split:])
    while line2 and draw.textlength(line2, font=font) > max_width:
        line2 = line2.rsplit(" ", 1)[0]
    if line2 != " ".join(words[best_split:]):
        line2 = line2.rstrip() + "..."
    return [line1, line2] if line2 else [line1]


def add_bottom_gradient(img: Image.Image, out_w: int, out_h: int, gradient_h: int) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(out_h - gradient_h, out_h):
        alpha = int(180 * (y - (out_h - gradient_h)) / gradient_h)
        draw.line([(0, y), (out_w, y)], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def draw_text_with_shadow(draw: ImageDraw.ImageDraw, pos: tuple[int, int], text: str, font, color: str):
    x, y = pos
    draw.text((x + 4, y + 4), text, font=font, fill=(0, 0, 0, 180), anchor="mt")
    draw.text((x, y), text, font=font, fill=color, anchor="mt")


def generate_thumbnail(base_image_path: str, title: str, output_path: str, platform: str = "youtube") -> None:
    spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["youtube"])
    out_w, out_h = spec["w"], spec["h"]
    font_size, gradient_h, padding = spec["font_size"], spec["gradient_h"], spec["padding"]

    img = Image.open(base_image_path)
    img_ratio = img.width / img.height
    target_ratio = out_w / out_h
    if img_ratio > target_ratio:
        new_h, new_w = out_h, int(img_ratio * out_h)
    else:
        new_w, new_h = out_w, int(out_w / img_ratio)

    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - out_w) // 2
    top = (new_h - out_h) // 2
    img = img.crop((left, top, left + out_w, top + out_h))

    img = add_bottom_gradient(img, out_w, out_h, gradient_h)
    draw = ImageDraw.Draw(img)
    font = load_font(font_size)
    lines = wrap_title(draw, title, font, out_w - padding * 2)

    line_height = font_size + 10
    text_top = out_h - 40 - len(lines) * line_height
    center_x = out_w // 2

    for i, line in enumerate(lines):
        draw_text_with_shadow(draw, (center_x, text_top + i * line_height), line, font, TEXT_COLOR)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(output_path, "JPEG", quality=95)
    print(f"Thumbnail saved: {output_path} ({out_w}x{out_h})")


if __name__ == "__main__":
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("Usage: python -m video.generate_thumbnail <base_image> <title> <output> [platform]")
        print("Platforms: youtube, vertical, tiktok, xiaohongshu, bilibili")
        sys.exit(1)
    generate_thumbnail(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) == 5 else "youtube")
