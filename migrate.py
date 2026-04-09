"""
マイグレーション実行スクリプト

使い方:
    python migrate.py

migrations/ ディレクトリ内の *.sql ファイルをファイル名順に実行する。
実行済みのマイグレーションは schema_migrations テーブルで管理され、
未適用のものだけが実行される。
"""

import os
import sys

from database import _get_connection

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def ensure_migrations_table(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4
        """)
    conn.commit()


def get_applied_versions(conn) -> set:
    with conn.cursor() as cursor:
        cursor.execute("SELECT version FROM schema_migrations")
        rows = cursor.fetchall()
    return {row["version"] for row in rows}


def get_migration_files() -> list[str]:
    if not os.path.isdir(MIGRATIONS_DIR):
        return []
    files = [f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")]
    return sorted(files)


def apply_migration(conn, filename: str, sql: str):
    with conn.cursor() as cursor:
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
        cursor.execute(
            "INSERT INTO schema_migrations (version) VALUES (%s)", (filename,)
        )
    conn.commit()


def main():
    conn = _get_connection()
    try:
        ensure_migrations_table(conn)
        applied = get_applied_versions(conn)
        files = get_migration_files()

        if not files:
            print("マイグレーションファイルが見つかりません")
            return

        pending = [f for f in files if f not in applied]

        if not pending:
            print("✅ 未適用のマイグレーションはありません")
            return

        for filename in pending:
            filepath = os.path.join(MIGRATIONS_DIR, filename)
            with open(filepath, encoding="utf-8") as f:
                sql = f.read()
            print(f"▶ {filename} を適用中...")
            try:
                apply_migration(conn, filename, sql)
                print(f"✅ {filename} 完了")
            except Exception as e:
                print(f"❌ {filename} 失敗: {e}", file=sys.stderr)
                sys.exit(1)

        print(f"\n✅ {len(pending)}件のマイグレーションを適用しました")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
