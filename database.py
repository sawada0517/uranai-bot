"""
🗄️ データベース管理 - ユーザー・占い履歴・課金情報
"""

import sqlite3
import json
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "tarot.db"


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)

    def _connect(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        """テーブル作成"""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                line_user_id TEXT PRIMARY KEY,
                is_premium INTEGER DEFAULT 0,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_user_id TEXT NOT NULL,
                cards TEXT NOT NULL,
                question TEXT DEFAULT '',
                reading_text TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (line_user_id) REFERENCES users(line_user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_readings_user_date
                ON readings(line_user_id, created_at);
        """)

        conn.commit()
        conn.close()
        print("✅ Database initialized")

    def upsert_user(self, line_user_id: str):
        conn = self._connect()
        conn.execute(
            """
            INSERT INTO users (line_user_id) VALUES (?)
            ON CONFLICT(line_user_id) DO UPDATE SET updated_at = datetime('now')
            """,
            (line_user_id,),
        )
        conn.commit()
        conn.close()

    def get_user(self, line_user_id: str) -> dict | None:
        conn = self._connect()
        row = conn.execute(
            "SELECT * FROM users WHERE line_user_id = ?", (line_user_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_user_by_subscription(self, subscription_id: str) -> dict | None:
        conn = self._connect()
        row = conn.execute(
            "SELECT * FROM users WHERE stripe_subscription_id = ?",
            (subscription_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def upgrade_to_premium(
        self, line_user_id: str, subscription_id: str, customer_id: str
    ):
        conn = self._connect()
        conn.execute(
            """
            UPDATE users SET
                is_premium = 1,
                stripe_subscription_id = ?,
                stripe_customer_id = ?,
                updated_at = datetime('now')
            WHERE line_user_id = ?
            """,
            (subscription_id, customer_id, line_user_id),
        )
        conn.commit()
        conn.close()

    def downgrade_from_premium(self, subscription_id: str):
        conn = self._connect()
        conn.execute(
            """
            UPDATE users SET
                is_premium = 0,
                stripe_subscription_id = NULL,
                updated_at = datetime('now')
            WHERE stripe_subscription_id = ?
            """,
            (subscription_id,),
        )
        conn.commit()
        conn.close()

    def save_reading(
        self, line_user_id: str, cards: list[dict], question: str, reading_text: str
    ):
        conn = self._connect()
        conn.execute(
            """
            INSERT INTO readings (line_user_id, cards, question, reading_text)
            VALUES (?, ?, ?, ?)
            """,
            (line_user_id, json.dumps(cards, ensure_ascii=False), question, reading_text),
        )
        conn.commit()
        conn.close()

    def get_today_reading_count(self, line_user_id: str) -> int:
        conn = self._connect()
        today = date.today().isoformat()
        row = conn.execute(
            """
            SELECT COUNT(*) as cnt FROM readings
            WHERE line_user_id = ? AND date(created_at) = ?
            """,
            (line_user_id, today),
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0

    def get_total_reading_count(self, line_user_id: str) -> int:
        conn = self._connect()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM readings WHERE line_user_id = ?",
            (line_user_id,),
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0
