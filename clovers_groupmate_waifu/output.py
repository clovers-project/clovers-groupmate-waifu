from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw
from linecard import FontManager, linecard, info_splicing


class LinecardDraw:
    def __init__(self, fontname: str, fallback: list[str], bg_image: Path | str) -> None:
        self.font_manager = FontManager(fontname, fallback, (30, 40, 60))
        self.bg_image = bg_image if isinstance(bg_image, Path) else Path(bg_image)

    def couple(self, title: str, data: list[tuple[bytes | None, str, bytes | None, str]]) -> BytesIO:
        canvas = Image.new("RGBA", (880, 80 * len(data) + 20))
        draw = ImageDraw.Draw(canvas)
        y = 20
        font = self.font_manager.font(40)
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
        textcard = linecard(title, self.font_manager, font_size=60, width=880)
        output = BytesIO()
        info_splicing([textcard, canvas], BG_path=self.bg_image, spacing=10, BG_type="GAUSS: 8").save(output, format="PNG")
        return output

    def waifu_list(self, title: str, data: list[tuple[bytes | None, str]]) -> BytesIO:
        canvas = Image.new("RGBA", (880, 80 * len(data) + 20))
        draw = ImageDraw.Draw(canvas)
        y = 20
        font = self.font_manager.font(40)
        circle_mask = Image.new("RGBA", (60, 60), (255, 255, 255, 0))
        ImageDraw.Draw(circle_mask).ellipse(((0, 0), (60, 60)), fill="black")
        for avatar, text in data:
            if avatar:
                canvas.paste(Image.open(BytesIO(avatar)).resize((60, 60)), (5, y), circle_mask)
            draw.text((80, y + 10), text, fill=(0, 0, 0), font=font)
            y += 80
        textcard = linecard(title, self.font_manager, font_size=60, width=880)
        output = BytesIO()
        info_splicing([textcard, canvas], BG_path=self.bg_image, spacing=10, BG_type="GAUSS: 8").save(output, format="PNG")
        return output

    def sese(self, title: str, data: list[tuple[bytes | None, str]]) -> BytesIO:
        canvas = Image.new("RGBA", (880, 80 * len(data) + 20))
        y = 20
        circle_mask = Image.new("RGBA", (60, 60), (255, 255, 255, 0))
        ImageDraw.Draw(circle_mask).ellipse(((0, 0), (60, 60)), fill="black")
        for avatar, text in data:
            if avatar:
                canvas.paste(Image.open(BytesIO(avatar)).resize((60, 60)), (5, y), circle_mask)
            canvas.paste(linecard(text, self.font_manager, font_size=40, width=800, padding=(0, 0)), (80, y + 10))
            y += 80
        textcard = linecard(title, self.font_manager, font_size=80, width=880)
        output = BytesIO()
        info_splicing([textcard, canvas], BG_path=self.bg_image, spacing=10, BG_type="GAUSS: 8").save(output, format="PNG")
        return output
