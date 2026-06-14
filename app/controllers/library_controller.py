"""书籍库控制器 - 业务逻辑层"""
from pathlib import Path
from typing import List, Optional

from ..models import Database, Book, Chapter
from ..utils import BookParser, CoverGenerator


class LibraryController:
    """书籍库业务逻辑"""

    def __init__(self, db: Database, cover_dir: Path):
        self.db = db
        self.parser = BookParser()
        self.cover_gen = CoverGenerator(cover_dir)

    def import_book(self, file_path: str) -> Optional[Book]:
        """导入本地 txt 书籍"""
        path = Path(file_path)
        if not path.exists():
            return None
        if path.suffix.lower() != ".txt":
            return None

        # 检查是否已导入
        existing = self.db.get_book_by_path(str(path.absolute()))
        if existing:
            return existing

        # 解析文件
        content, chapters = self.parser.parse_txt(str(path))
        meta = self.parser.extract_metadata(str(path), content)

        # 生成封面
        cover_path = self.cover_gen.generate(meta["title"], meta["author"])

        book = Book(
            title=meta["title"],
            author=meta["author"],
            file_path=str(path.absolute()),
            cover_path=cover_path,
            description=meta["description"],
            total_chars=len(content),
            chapter_count=len(chapters),
            chapters=chapters,
        )
        book.id = self.db.add_book(book)
        return book

    def remove_book(self, book_id: int, delete_cover: bool = True):
        """从书架删除书籍（不删源文件）

        Args:
            book_id: 书籍 ID
            delete_cover: 是否同时删除本程序生成的封面缓存
                          （仅当封面位于我们的 covers/ 目录内时才会真删）
        """
        book = self.db.get_book(book_id)
        # 先删数据库（外键级联会清掉书签 / 统计）
        self.db.delete_book(book_id)
        # 同步删除本应用生成的封面缓存
        if delete_cover and book and book.cover_path:
            cover = Path(book.cover_path)
            try:
                # 仅当封面位于本应用 covers 目录内时删除
                if cover.parent == self.cover_gen.cover_dir and cover.exists():
                    cover.unlink()
            except OSError:
                # 封面文件被占用或权限不足时静默忽略，不影响主流程
                pass

    def get_all_books(self) -> List[Book]:
        """获取所有书籍"""
        return self.db.get_all_books()

    def get_book(self, book_id: int) -> Optional[Book]:
        return self.db.get_book(book_id)

    def update_progress(self, book: Book, chapter_index: int, position: int,
                        total_chars: int):
        """更新阅读进度"""
        from datetime import datetime
        book.current_chapter = chapter_index
        book.current_position = position
        if total_chars > 0:
            book.progress = min(1.0, max(0.0, position / total_chars))
        book.last_read_at = datetime.now().isoformat()
        self.db.update_book(book)

    def toggle_favorite(self, book: Book):
        book.is_favorite = not book.is_favorite
        self.db.update_book(book)
        return book.is_favorite
