import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional


class SQLiteStore:
    def __init__(self, path: Optional[str] = None):
        db_path = path or os.environ.get("MALAYA_DB_PATH", "data/malaya.db")
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS response_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at REAL,
                    ttl INTEGER
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at REAL,
                    ttl INTEGER
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS project_memory (
                    project_id TEXT PRIMARY KEY,
                    summary TEXT,
                    message_count INTEGER,
                    updated_at REAL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS shares (
                    share_id TEXT PRIMARY KEY,
                    share_type TEXT,
                    payload TEXT,
                    created_at REAL,
                    expires_at REAL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    message_id TEXT,
                    rating TEXT,
                    comment TEXT,
                    model_provider TEXT,
                    model_name TEXT,
                    metadata TEXT,
                    created_at REAL
                )
                """
            )
            self._conn.commit()

    def _cache_get(self, table: str, key: str) -> Optional[str]:
        now = time.time()
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                f"SELECT value, created_at, ttl FROM {table} WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            ttl = row["ttl"] or 0
            if ttl and row["created_at"] + ttl < now:
                cursor.execute(f"DELETE FROM {table} WHERE key = ?", (key,))
                self._conn.commit()
                return None
            return row["value"]

    def _cache_set(self, table: str, key: str, value: Any, ttl: int) -> None:
        payload = json.dumps(value, ensure_ascii=True)
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {table} (key, value, created_at, ttl)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, created_at=excluded.created_at, ttl=excluded.ttl
                """,
                (key, payload, time.time(), int(ttl)),
            )
            self._conn.commit()

    def response_cache_get(self, key: str) -> Optional[dict]:
        raw = self._cache_get("response_cache", key)
        return json.loads(raw) if raw else None

    def response_cache_set(self, key: str, value: dict, ttl: int) -> None:
        self._cache_set("response_cache", key, value, ttl)

    def tool_cache_get(self, key: str) -> Optional[str]:
        return self._cache_get("tool_cache", key)

    def tool_cache_set(self, key: str, value: str, ttl: int) -> None:
        self._cache_set("tool_cache", key, value, ttl)

    def get_project_memory(self, project_id: str) -> Optional[dict]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT summary, message_count, updated_at FROM project_memory WHERE project_id = ?",
                (project_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "summary": row["summary"],
                "message_count": row["message_count"],
                "updated_at": row["updated_at"],
            }

    def set_project_memory(self, project_id: str, summary: str, message_count: int) -> None:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO project_memory (project_id, summary, message_count, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET summary=excluded.summary, message_count=excluded.message_count, updated_at=excluded.updated_at
                """,
                (project_id, summary, int(message_count), time.time()),
            )
            self._conn.commit()

    def clear_project_memory(self, project_id: str) -> None:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "DELETE FROM project_memory WHERE project_id = ?",
                (project_id,),
            )
            self._conn.commit()

    def create_share(self, share_id: str, share_type: str, payload: dict, ttl_seconds: int) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO shares (share_id, share_type, payload, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(share_id) DO UPDATE SET payload=excluded.payload, created_at=excluded.created_at, expires_at=excluded.expires_at
                """,
                (share_id, share_type, json.dumps(payload, ensure_ascii=True), time.time(), expires_at),
            )
            self._conn.commit()

    def get_share(self, share_id: str) -> Optional[dict]:
        now = time.time()
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT share_type, payload, expires_at FROM shares WHERE share_id = ?",
                (share_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            expires_at = row["expires_at"]
            if expires_at and expires_at < now:
                cursor.execute("DELETE FROM shares WHERE share_id = ?", (share_id,))
                self._conn.commit()
                return None
            return {
                "share_type": row["share_type"],
                "payload": json.loads(row["payload"]),
                "expires_at": expires_at,
            }

    def create_feedback(
        self,
        feedback_id: str,
        conversation_id: Optional[str],
        message_id: Optional[str],
        rating: Optional[str],
        comment: Optional[str],
        model_provider: Optional[str],
        model_name: Optional[str],
        metadata: Optional[dict] = None,
    ) -> None:
        payload = json.dumps(metadata or {}, ensure_ascii=True)
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO feedback (
                    feedback_id,
                    conversation_id,
                    message_id,
                    rating,
                    comment,
                    model_provider,
                    model_name,
                    metadata,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback_id,
                    conversation_id,
                    message_id,
                    rating,
                    comment,
                    model_provider,
                    model_name,
                    payload,
                    time.time(),
                ),
            )
            self._conn.commit()

    def get_feedback(self, feedback_id: str) -> Optional[dict]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT
                    conversation_id,
                    message_id,
                    rating,
                    comment,
                    model_provider,
                    model_name,
                    metadata,
                    created_at
                FROM feedback
                WHERE feedback_id = ?
                """,
                (feedback_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "conversation_id": row["conversation_id"],
                "message_id": row["message_id"],
                "rating": row["rating"],
                "comment": row["comment"],
                "model_provider": row["model_provider"],
                "model_name": row["model_name"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"],
            }

    def list_feedback(self, limit: int = 20) -> list[dict]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT
                    feedback_id,
                    conversation_id,
                    message_id,
                    rating,
                    comment,
                    model_provider,
                    model_name,
                    metadata,
                    created_at
                FROM feedback
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            rows = cursor.fetchall()
            results = []
            for row in rows or []:
                results.append({
                    "feedback_id": row["feedback_id"],
                    "conversation_id": row["conversation_id"],
                    "message_id": row["message_id"],
                    "rating": row["rating"],
                    "comment": row["comment"],
                    "model_provider": row["model_provider"],
                    "model_name": row["model_name"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"],
                })
            return results

    def feedback_summary(self) -> dict:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM feedback")
            total = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) AS total FROM feedback WHERE rating = 'up'")
            total_up = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) AS total FROM feedback WHERE rating = 'down'")
            total_down = cursor.fetchone()["total"]
            return {
                "total": total,
                "up": total_up,
                "down": total_down,
            }
