"""自动封面生成器 - 无封面时使用 PIL 绘制一张带渐变和书名的封面"""
import hashlib
from pathlib import Path
from typing import Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# 渐变色板（按 hash 选择）
GRADIENTS = [
    ((99, 102, 241), (236, 72, 153)),    # indigo -> pink
    ((59, 130, 246), (16, 185, 129)),    # blue -> green
    ((245, 158, 11), (239, 68, 68)),     # amber -> red
    ((139, 92, 246), (59, 130, 246)),    # purple -> blue
    ((14, 165, 233), (99, 102, 241)),    # sky -> indigo
    ((236, 72, 153), (251, 146, 60)),    # pink -> orange
    ((34, 197, 94), (59, 130, 246)),     # green -> blue
    ((168, 85, 247), (236, 72, 153)),    # purple -> pink
    ((251, 113, 133), (217, 70, 239)),   # rose -> fuchsia
    ((20, 184, 166), (59, 130, 246)),    # teal -> blue
]


class CoverGenerator:
    """自动生成书籍封面"""

    WIDTH = 240
    HEIGHT = 320

    def __init__(self, cover_dir: Path):
        self.cover_dir = cover_dir
        cover_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, title: str, author: str) -> str:
        """为指定书籍生成封面，返回封面文件路径"""
        if not HAS_PIL:
            return ""

        # 用标题生成稳定 hash 决定颜色
        key = f"{title}{author}".encode("utf-8")
        h = int(hashlib.md5(key).hexdigest(), 16)
        color1, color2 = GRADIENTS[h % len(GRADIENTS)]

        # 文件名
        name_hash = hashlib.md5(key).hexdigest()[:12]
        cover_path = self.cover_dir / f"{name_hash}.png"
        if cover_path.exists():
            return str(cover_path)

        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), color1)
        draw = ImageDraw.Draw(img)

        # 绘制垂直渐变
        for y in range(self.HEIGHT):
            ratio = y / self.HEIGHT
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.line([(0, y), (self.WIDTH, y)], fill=(r, g, b))

        # 装饰几何图形
        for i in range(3):
            alpha = 40 - i * 10
            draw.ellipse(
                [self.WIDTH - 100 - i * 30, -50 - i * 30,
                 self.WIDTH + 20 - i * 30, 70 - i * 30],
                outline=(255, 255, 255, alpha), width=2
            )

        # 绘制标题
        font_title = self._get_font(28)
        font_author = self._get_font(16)

        title_lines = self._wrap_text(title, font_title, self.WIDTH - 40)
        y = self.HEIGHT // 2 - 20
        for line in title_lines[:3]:
            bbox = draw.textbbox((0, 0), line, font=font_title)
            w = bbox[2] - bbox[0]
            draw.text(((self.WIDTH - w) / 2, y), line,
                      fill=(255, 255, 255), font=font_title)
            y += 36

        # 绘制作者
        bbox = draw.textbbox((0, 0), author, font=font_author)
        w = bbox[2] - bbox[0]
        draw.text(((self.WIDTH - w) / 2, self.HEIGHT - 50), author,
                  fill=(255, 255, 255, 200), font=font_author)

        img.save(cover_path, "PNG")
        return str(cover_path)

    def _get_font(self, size: int):
        """获取中文字体"""
        candidates = [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\msyh.ttf",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        for path in candidates:
            if Path(path).exists():
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def _wrap_text(self, text: str, font, max_width: int) -> list:
        """简单文本换行（按字符宽度估算）"""
        lines = []
        current = ""
        for ch in text:
            test = current + ch
            try:
                bbox = font.getbbox(test)
                w = bbox[2] - bbox[0]
            except Exception:
                w = len(test) * font.size
            if w > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
        return lines
