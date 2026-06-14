"""书籍解析器 - 解析 txt 文件并切分章节"""
import re
from pathlib import Path
from typing import List, Tuple

from ..models.book import Chapter


class BookParser:
    """txt 小说解析器"""

    # 章节标题正则 - 兼容多种格式
    # 第一章 / 第1章 / Chapter 1 / 楔子 / 序言 / 番外 / 终章 等
    CHAPTER_PATTERNS = [
        re.compile(r'^\s*第\s*([0-9零一二三四五六七八九十百千万]+|[\d]+)\s*[章回节卷][\s\S]*$'),
        re.compile(r'^\s*Chapter\s+\d+[\s\S]*$', re.IGNORECASE),
        re.compile(r'^\s*楔\s*子\s*$'),
        re.compile(r'^\s*序\s*言\s*$'),
        re.compile(r'^\s*序\s*章\s*$'),
        re.compile(r'^\s*引\s*子\s*$'),
        re.compile(r'^\s*后\s*记\s*$'),
        re.compile(r'^\s*番\s*外\s*[\d]*\s*$'),
        re.compile(r'^\s*终\s*章\s*$'),
        re.compile(r'^\s*尾\s*声\s*$'),
        re.compile(r'^\s*结\s*局\s*$'),
        re.compile(r'^\s*[卷集部]\s*[一二三四五六七八九十0-9]+\s*$'),
    ]

    @classmethod
    def parse_txt(cls, file_path: str) -> Tuple[str, List[Chapter]]:
        """解析 txt 文件，返回(全文, 章节列表)"""
        path = Path(file_path)
        # 尝试不同编码
        content = None
        for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb18030', 'big5']:
            try:
                content = path.read_text(encoding=encoding)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        if content is None:
            raise ValueError(f"无法识别文件编码: {file_path}")

        # 统一换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        # 去除每行末尾空白
        lines = content.split('\n')

        chapters = cls._split_chapters(lines)

        # 如果没有检测到章节，把整本书作为一章
        if not chapters:
            chapters = [Chapter(
                index=0,
                title=path.stem,
                start_pos=0,
                end_pos=len(content),
                word_count=len(content.strip())
            )]
        else:
            # 补全章节的 end_pos 和 word_count
            for i, ch in enumerate(chapters):
                if i + 1 < len(chapters):
                    ch.end_pos = chapters[i + 1].start_pos
                else:
                    ch.end_pos = len(content)
                ch.word_count = ch.end_pos - ch.start_pos

        return content, chapters

    @classmethod
    def _split_chapters(cls, lines: List[str]) -> List[Chapter]:
        """根据行内容切分章节"""
        chapters = []
        current_pos = 0
        for line in lines:
            stripped = line.strip()
            if cls._is_chapter_title(stripped):
                chapters.append(Chapter(
                    index=len(chapters),
                    title=stripped,
                    start_pos=current_pos,
                ))
            current_pos += len(line) + 1  # +1 for '\n'
        return chapters

    @classmethod
    def _is_chapter_title(cls, line: str) -> bool:
        """判断是否为章节标题"""
        if not line or len(line) > 50:
            return False
        for pattern in cls.CHAPTER_PATTERNS:
            if pattern.match(line):
                return True
        return False

    @staticmethod
    def extract_metadata(file_path: str, content: str) -> dict:
        """从文件路径和内容中提取元数据"""
        path = Path(file_path)
        title = path.stem

        author = "未知作者"
        # 尝试从内容前 30 行提取作者信息
        head = '\n'.join(content.split('\n')[:30])
        # 作者：xxx（截取到空白、特殊符号或长度限制前）
        author_match = re.search(r'作\s*者[：:]\s*([^\n\r]{1,40})', head)
        if author_match:
            raw = author_match.group(1).strip()
            # 截断到第一个空格、逗号、破折号或"生成"等关键词
            cut_match = re.search(r'^([^\s,，—\-=_*#生成]+)', raw)
            author = cut_match.group(1) if cut_match else raw[:20]

        # 尝试从内容中提取简介（寻找"简介"或"内容简介"后到下一章节前的内容）
        description = ""
        desc_match = re.search(r'(?:简介|内容简介|作品简介)[：:]?\s*([\s\S]{20,800}?)(?:\n\n|第\s*[0-9])', head)
        if desc_match:
            description = desc_match.group(1).strip()[:500]

        return {
            "title": title,
            "author": author,
            "description": description,
        }
