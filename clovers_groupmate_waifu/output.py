from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw
from clovers_utils.linecard import FontManager, linecard, info_splicing
from .config import waifu_config

fontname = waifu_config.fontname
fallback = waifu_config.fallback_fonts
bg_image = Path(waifu_config.bg_image)

font_manager = FontManager(fontname, fallback, (30, 40, 60))


def draw_couple(title: str, data: list[tuple[bytes | None, str, bytes | None, str]]) -> BytesIO:
    canvas = Image.new("RGBA", (880, 80 * len(data) + 20))
    draw = ImageDraw.Draw(canvas)
    y = 20
    font = font_manager.font(40)
    circle_mask = Image.new("RGBA", (60, 60), (255, 255, 255, 0))
    ImageDraw.Draw(circle_mask).ellipse(((0, 0), (60, 60)), fill="black")
    for avatar1, text1, avatar0, text0 in data:
        if avatar1:
            canvas.paste(Image.open(BytesIO(avatar1)).resize((60, 60)), (5, y), circle_mask)
        if avatar0:
            canvas.paste(Image.open(BytesIO(avatar0)).resize((60, 60)), (445, y), circle_mask)
        draw.text((80, y + 10), text1, fill=(0, 0, 0), font=font)
        draw.text((520, y + 10), text0, fill=(0, 0, 0), font=font)
        y += 80
    textcard = linecard(title, font_manager, font_size=60, width=880)
    return info_splicing([textcard, canvas], BG_path=bg_image, spacing=10, BG_type="GAUSS: 8")


def draw_list(title: str, data: list[tuple[bytes | None, str]]) -> BytesIO:
    canvas = Image.new("RGBA", (880, 80 * len(data) + 20))
    draw = ImageDraw.Draw(canvas)
    y = 20
    font = font_manager.font(40)
    circle_mask = Image.new("RGBA", (60, 60), (255, 255, 255, 0))
    ImageDraw.Draw(circle_mask).ellipse(((0, 0), (60, 60)), fill="black")
    for avatar, text in data:
        if avatar:
            canvas.paste(Image.open(BytesIO(avatar)).resize((60, 60)), (5, y), circle_mask)
        draw.text((80, y + 10), text, fill=(0, 0, 0), font=font)
        y += 80
    textcard = linecard(title, font_manager, font_size=60, width=880)
    return info_splicing([textcard, canvas], BG_path=bg_image, spacing=10, BG_type="GAUSS: 8")


def draw_sese(title: str, data: list[tuple[bytes | None, str]]):
    canvas = Image.new("RGBA", (880, 80 * len(data) + 20))
    y = 20
    circle_mask = Image.new("RGBA", (60, 60), (255, 255, 255, 0))
    ImageDraw.Draw(circle_mask).ellipse(((0, 0), (60, 60)), fill="black")
    for avatar, text in data:
        if avatar:
            canvas.paste(Image.open(BytesIO(avatar)).resize((60, 60)), (5, y), circle_mask)
        canvas.paste(linecard(text, font_manager, font_size=40, width=800, padding=(0, 0)), (80, y + 10))
        y += 80
    textcard = linecard(title, font_manager, font_size=80, width=880)
    return info_splicing([textcard, canvas], BG_path=bg_image, spacing=10, BG_type="GAUSS: 8")
