"""
🗄️ データベース管理 - ユーザー・占い履歴・課金情報
"""

import json
import os
from datetime import date

import pymysql
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()


def _get_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "uranai_bot"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


class Database:
    def __init__(self):
        pass

    def initialize(self):
        """テーブル作成"""
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        line_user_id VARCHAR(255) PRIMARY KEY,
                        is_premium TINYINT(1) NOT NULL DEFAULT 0,
                        stripe_customer_id VARCHAR(255),
                        stripe_subscription_id VARCHAR(255),
                        birth_date DATE NULL DEFAULT NULL,
                        gender VARCHAR(10) NULL DEFAULT NULL,
                        onboarding_step TINYINT NOT NULL DEFAULT 0,
                        morning_notify TINYINT(1) NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        deleted_at DATETIME NULL DEFAULT NULL
                    ) CHARACTER SET utf8mb4
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS readings (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        line_user_id VARCHAR(255) NOT NULL,
                        cards JSON NOT NULL,
                        question TEXT NULL,
                        reading_text TEXT NOT NULL,
                        feedback VARCHAR(10) NULL DEFAULT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_readings_user_date (line_user_id, created_at),
                        FOREIGN KEY (line_user_id) REFERENCES users(line_user_id)
                    ) CHARACTER SET utf8mb4
                """)
            conn.commit()
            print("✅ Database initialized")
        finally:
            conn.close()

    # ─── ユーザー管理 ──────────────────────────────────────
    def upsert_user(self, line_user_id: str):
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (line_user_id) VALUES (%s)
                    ON DUPLICATE KEY UPDATE
                        deleted_at = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (line_user_id,),
                )
            conn.commit()
        finally:
            conn.close()

    def delete_user(self, line_user_id: str):
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE line_user_id = %s",
                    (line_user_id,),
                )
            conn.commit()
        finally:
            conn.close()

    def get_user(self, line_user_id: str) -> dict | None:
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE line_user_id = %s", (line_user_id,)
                )
                return cursor.fetchone()
        finally:
            conn.close()

    def get_user_by_subscription(self, subscription_id: str) -> dict | None:
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE stripe_subscription_id = %s",
                    (subscription_id,),
                )
                return cursor.fetchone()
        finally:
            conn.close()

    def update_birth_date(self, line_user_id: str, birth_date: str):
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET birth_date = %s, onboarding_step = 2 WHERE line_user_id = %s",
                    (birth_date, line_user_id),
                )
            conn.commit()
        finally:
            conn.close()

    def update_gender(self, line_user_id: str, gender: str):
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET gender = %s, onboarding_step = 0 WHERE line_user_id = %s",
                    (gender, line_user_id),
                )
            conn.commit()
        finally:
            conn.close()

    def set_morning_notify(self, line_user_id: str, enabled: bool):
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET morning_notify = %s WHERE line_user_id = %s",
                    (1 if enabled else 0, line_user_id),
                )
            conn.commit()
        finally:
            conn.close()

    def get_morning_notify_users(self) -> list[dict]:
        """朝の通知が有効なユーザー一覧を返す"""
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT line_user_id, birth_date, gender
                    FROM users
                    WHERE morning_notify = 1 AND deleted_at IS NULL
                    """
                )
                return cursor.fetchall()
        finally:
            conn.close()

    def set_onboarding_step(self, line_user_id: str, step: int):
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET onboarding_step = %s WHERE line_user_id = %s",
                    (step, line_user_id),
                )
            conn.commit()
        finally:
            conn.close()

    # ─── 課金管理 ──────────────────────────────────────────
    def upgrade_to_premium(
        self, line_user_id: str, subscription_id: str, customer_id: str
    ):
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users SET
                        is_premium = 1,
                        stripe_subscription_id = %s,
                        stripe_customer_id = %s
                    WHERE line_user_id = %s
                    """,
                    (subscription_id, customer_id, line_user_id),
                )
            conn.commit()
        finally:
            conn.close()

    def downgrade_from_premium(self, subscription_id: str):
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users SET
                        is_premium = 0,
                        stripe_subscription_id = NULL
                    WHERE stripe_subscription_id = %s
                    """,
                    (subscription_id,),
                )
            conn.commit()
        finally:
            conn.close()

    # ─── 占い履歴 ─────────────────────────────────────────
    def save_reading(
        self, line_user_id: str, cards: list[dict], question: str, reading_text: str
    ):
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO readings (line_user_id, cards, question, reading_text)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (line_user_id, json.dumps(cards, ensure_ascii=False), question, reading_text),
                )
            conn.commit()
        finally:
            conn.close()

    def get_pending_feedback(self, line_user_id: str) -> dict | None:
        """最新のreadingでfeedbackが未取得ならそのreadingを返す。なければNone"""
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, reading_text FROM readings
                    WHERE line_user_id = %s AND feedback IS NULL
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (line_user_id,),
                )
                row = cursor.fetchone()
                if row:
                    return {"reading_id": row["id"], "pending": True}
                return None
        finally:
            conn.close()

    def save_feedback(self, line_user_id: str, reading_id: int, feedback_value: str):
        """feedbackを保存する。feedback_valueは 'good' / 'maybe' / 'miss' のいずれか"""
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE readings SET feedback = %s
                    WHERE id = %s AND line_user_id = %s
                    """,
                    (feedback_value, reading_id, line_user_id),
                )
            conn.commit()
        finally:
            conn.close()

    def get_last_reading_with_feedback(self, line_user_id: str) -> dict | None:
        """feedbackが記録された最新のreadingを返す"""
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT feedback FROM readings
                    WHERE line_user_id = %s AND feedback IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (line_user_id,),
                )
                return cursor.fetchone()
        finally:
            conn.close()

    def get_today_reading_count(self, line_user_id: str) -> int:
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                today = date.today().isoformat()
                cursor.execute(
                    """
                    SELECT COUNT(*) AS cnt FROM readings
                    WHERE line_user_id = %s AND DATE(created_at) = %s
                    """,
                    (line_user_id, today),
                )
                row = cursor.fetchone()
                return row["cnt"] if row else 0
        finally:
            conn.close()

    def get_total_reading_count(self, line_user_id: str) -> int:
        conn = _get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM readings WHERE line_user_id = %s",
                    (line_user_id,),
                )
                row = cursor.fetchone()
                return row["cnt"] if row else 0
        finally:
            conn.close()
