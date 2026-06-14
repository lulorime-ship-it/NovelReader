"""SQLite 数据库管理 - 持久化书籍、阅读进度、书签"""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .book import Book, Chapter, Bookmark


class Database:
    """数据库管理类"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT,
                    file_path TEXT UNIQUE NOT NULL,
                    cover_path TEXT,
                    description TEXT,
                    total_chars INTEGER DEFAULT 0,
                    chapter_count INTEGER DEFAULT 0,
                    chapters_json TEXT,
                    current_chapter INTEGER DEFAULT 0,
                    current_position INTEGER DEFAULT 0,
                    progress REAL DEFAULT 0,
                    added_at TEXT,
                    last_read_at TEXT,
                    is_favorite INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    chapter_index INTEGER,
                    chapter_title TEXT,
                    position INTEGER,
                    note TEXT,
                    created_at TEXT,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS reading_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    date TEXT,
                    duration_seconds INTEGER DEFAULT 0,
                    chars_read INTEGER DEFAULT 0,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_bookmarks_book ON bookmarks(book_id);
                CREATE INDEX IF NOT EXISTS idx_stats_book ON reading_stats(book_id);
            """)

    # ---------- 书籍操作 ----------
    def add_book(self, book: Book) -> int:
        with self._get_conn() as conn:
            chapters_json = json.dumps([c.to_dict() for c in book.chapters], ensure_ascii=False)
            cur = conn.execute("""
                INSERT INTO books (title, author, file_path, cover_path, description,
                                   total_chars, chapter_count, chapters_json, added_at, last_read_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (book.title, book.author, book.file_path, book.cover_path,
                  book.description, book.total_chars, book.chapter_count,
                  chapters_json, book.added_at, book.last_read_at))
            book.id = cur.lastrowid
            return book.id

    def update_book(self, book: Book):
        chapters_json = json.dumps([c.to_dict() for c in book.chapters], ensure_ascii=False)
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE books SET title=?, author=?, cover_path=?, description=?,
                                 total_chars=?, chapter_count=?, chapters_json=?,
                                 current_chapter=?, current_position=?, progress=?,
                                 last_read_at=?, is_favorite=?
                WHERE id=?
            """, (book.title, book.author, book.cover_path, book.description,
                  book.total_chars, book.chapter_count, chapters_json,
                  book.current_chapter, book.current_position, book.progress,
                  book.last_read_at, int(book.is_favorite), book.id))

    def delete_book(self, book_id: int):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM books WHERE id=?", (book_id,))

    def get_all_books(self) -> List[Book]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM books ORDER BY last_read_at DESC, added_at DESC"
            ).fetchall()
            return [self._row_to_book(r) for r in rows]

    def get_book(self, book_id: int) -> Optional[Book]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
            return self._row_to_book(row) if row else None

    def get_book_by_path(self, file_path: str) -> Optional[Book]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM books WHERE file_path=?",
                               (str(file_path),)).fetchone()
            return self._row_to_book(row) if row else None

    def _row_to_book(self, row) -> Book:
        chapters = []
        if row["chapters_json"]:
            try:
                chapters_data = json.loads(row["chapters_json"])
                chapters = [Chapter(**c) for c in chapters_data]
            except (json.JSONDecodeError, TypeError):
                chapters = []
        return Book(
            id=row["id"],
            title=row["title"],
            author=row["author"] or "未知作者",
            file_path=row["file_path"],
            cover_path=row["cover_path"] or "",
            description=row["description"] or "",
            total_chars=row["total_chars"] or 0,
            chapter_count=row["chapter_count"] or 0,
            current_chapter=row["current_chapter"] or 0,
            current_position=row["current_position"] or 0,
            progress=row["progress"] or 0.0,
            added_at=row["added_at"] or "",
            last_read_at=row["last_read_at"] or "",
            is_favorite=bool(row["is_favorite"]),
            chapters=chapters,
        )

    # ---------- 书签操作 ----------
    def add_bookmark(self, bm: Bookmark) -> int:
        with self._get_conn() as conn:
            cur = conn.execute("""
                INSERT INTO bookmarks (book_id, chapter_index, chapter_title, position, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (bm.book_id, bm.chapter_index, bm.chapter_title, bm.position, bm.note, bm.created_at))
            return cur.lastrowid

    def delete_bookmark(self, bookmark_id: int):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM bookmarks WHERE id=?", (bookmark_id,))

    def get_bookmarks(self, book_id: int) -> List[Bookmark]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM bookmarks WHERE book_id=? ORDER BY created_at DESC",
                (book_id,)
            ).fetchall()
            return [Bookmark(
                id=r["id"], book_id=r["book_id"],
                chapter_index=r["chapter_index"], chapter_title=r["chapter_title"] or "",
                position=r["position"] or 0, note=r["note"] or "",
                created_at=r["created_at"] or "",
            ) for r in rows]

    # ---------- 设置 ----------
    def get_setting(self, key: str, default: str = "") -> str:
        with self._get_conn() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )

    def get_all_settings(self) -> dict:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {r["key"]: r["value"] for r in rows}

    # ---------- 统计 ----------
    def record_reading(self, book_id: int, duration: int, chars: int):
        today = datetime.now().strftime("%Y-%m-%d")
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO reading_stats (book_id, date, duration_seconds, chars_read)
                VALUES (?, ?, ?, ?)
            """, (book_id, today, duration, chars))

    def get_today_reading(self) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT COALESCE(SUM(duration_seconds), 0) AS dur,
                       COALESCE(SUM(chars_read), 0) AS chars
                FROM reading_stats WHERE date=?
            """, (today,)).fetchone()
            return {"duration": row["dur"], "chars": row["chars"]}

    def get_total_stats(self) -> dict:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT COALESCE(SUM(duration_seconds), 0) AS dur,
                       COALESCE(SUM(chars_read), 0) AS chars,
                       COUNT(DISTINCT book_id) AS book_count
                FROM reading_stats
            """).fetchone()
            book_row = conn.execute("SELECT COUNT(*) AS cnt FROM books").fetchone()
            return {
                "duration": row["dur"],
                "chars": row["chars"],
                "books_read": row["book_count"],
                "total_books": book_row["cnt"],
            }
