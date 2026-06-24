import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.schemas.log_analysis import LogAnalysis, LogInput, StoredLogAnalysis


class LogAnalysisRepository:
    """SQLite repository for persisted log analyses."""

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS log_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    raw_log TEXT NOT NULL,
                    language TEXT NOT NULL,
                    source TEXT NOT NULL,
                    analysis_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def save(self, log_input: LogInput, analysis: LogAnalysis) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO log_analyses (
                    title, raw_log, language, source, analysis_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    log_input.title,
                    log_input.raw_log,
                    log_input.language,
                    log_input.source,
                    analysis.model_dump_json(),
                    created_at,
                ),
            )
            return int(cursor.lastrowid)

    def list_all(self) -> list[StoredLogAnalysis]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, raw_log, language, source, analysis_json, created_at
                FROM log_analyses
                ORDER BY id DESC
                """
            ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def get(self, analysis_id: int) -> StoredLogAnalysis | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, title, raw_log, language, source, analysis_json, created_at
                FROM log_analyses
                WHERE id = ?
                """,
                (analysis_id,),
            ).fetchone()
        return self._row_to_model(row) if row else None

    def delete(self, analysis_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM log_analyses WHERE id = ?", (analysis_id,))
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> StoredLogAnalysis:
        return StoredLogAnalysis(
            id=row["id"],
            title=row["title"],
            raw_log=row["raw_log"],
            language=row["language"],
            source=row["source"],
            analysis=LogAnalysis.model_validate(json.loads(row["analysis_json"])),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
