"""书籍数据模型"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class Chapter:
    """章节数据"""
    index: int
    title: str
    start_pos: int  # 章节在原文中的起始字符位置
    end_pos: int = 0  # 章节在原文中的结束位置
    word_count: int = 0

    def to_dict(self):
        return asdict(self)


@dataclass
class Bookmark:
    """书签"""
    id: int = 0
    book_id: int = 0
    chapter_index: int = 0
    chapter_title: str = ""
    position: int = 0  # 字符位置
    note: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        return asdict(self)


@dataclass
class Book:
    """书籍数据模型"""
    id: int = 0
    title: str = ""
    author: str = "未知作者"
    file_path: str = ""
    cover_path: str = ""
    description: str = ""
    total_chars: int = 0
    chapter_count: int = 0
    current_chapter: int = 0
    current_position: int = 0
    progress: float = 0.0  # 阅读进度 0-1
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_read_at: str = ""
    is_favorite: bool = False
    chapters: List[Chapter] = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["chapters"] = [c.to_dict() for c in self.chapters]
        return d
