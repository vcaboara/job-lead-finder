import logging
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DATA_DIR = Path("/app/data") if Path("/app/data").exists() else Path(".")
DB_PATH = _DATA_DIR / "job_runs.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS job_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    trigger TEXT NOT NULL,
    query TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    error TEXT
);
CREATE TABLE IF NOT EXISTS provider_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES job_runs(run_id),
    provider TEXT NOT NULL,
    jobs_found INTEGER NOT NULL DEFAULT 0,
    jobs_new INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER,
    error TEXT
);
CREATE INDEX IF NOT EXISTS idx_job_runs_started_at ON job_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_provider_results_run_id ON provider_results(run_id);
"""


class JobRunRecorder:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def start_run(self, trigger: str, query: Optional[str] = None) -> str:
        run_id = str(uuid.uuid4())
        conn = self._connect()
        conn.execute(
            "INSERT INTO job_runs (run_id, started_at, trigger, query, status) VALUES (?, ?, ?, ?, 'running')",
            (run_id, datetime.now(timezone.utc).isoformat(), trigger, query),
        )
        conn.commit()
        logger.debug("Started run %s trigger=%s query=%s", run_id, trigger, query)
        return run_id

    def record_provider(
        self,
        run_id: str,
        provider: str,
        jobs_found: int,
        jobs_new: int,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        conn = self._connect()
        conn.execute(
            "INSERT INTO provider_results (run_id, provider, jobs_found, jobs_new, duration_ms, error)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, provider, jobs_found, jobs_new, duration_ms, error),
        )
        conn.commit()

    def finish_run(self, run_id: str, status: str = "completed", error: Optional[str] = None) -> None:
        conn = self._connect()
        conn.execute(
            "UPDATE job_runs SET finished_at=?, status=?, error=? WHERE run_id=?",
            (datetime.now(timezone.utc).isoformat(), status, error, run_id),
        )
        conn.commit()
        logger.debug("Finished run %s status=%s", run_id, status)

    def get_recent_runs(self, limit: int = 20) -> list[dict]:
        rows = (
            self._connect()
            .execute(
                """
            SELECT r.run_id, r.started_at, r.finished_at, r.trigger, r.query, r.status, r.error,
                   COALESCE(SUM(p.jobs_found), 0) AS jobs_found,
                   COALESCE(SUM(p.jobs_new), 0) AS jobs_new
            FROM job_runs r
            LEFT JOIN provider_results p ON r.run_id = p.run_id
            GROUP BY r.run_id
            ORDER BY r.started_at DESC
            LIMIT ?
            """,
                (limit,),
            )
            .fetchall()
        )
        return [dict(r) for r in rows]

    def get_summary(self) -> dict:
        conn = self._connect()

        total = conn.execute("SELECT COUNT(*) FROM job_runs WHERE status = 'completed'").fetchone()[0]

        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        jobs_7d = conn.execute(
            """
            SELECT COALESCE(SUM(p.jobs_new), 0)
            FROM provider_results p
            JOIN job_runs r ON p.run_id = r.run_id
            WHERE r.started_at >= ?
            """,
            (cutoff,),
        ).fetchone()[0]

        top_row = conn.execute(
            """
            SELECT provider, SUM(jobs_found) AS total
            FROM provider_results
            GROUP BY provider
            ORDER BY total DESC
            LIMIT 1
            """,
        ).fetchone()

        return {
            "total_completed_runs": total,
            "jobs_new_last_7d": jobs_7d,
            "top_provider": dict(top_row) if top_row else None,
        }

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
