"""
DatabaseManager: SQLite veritabanı işlemlerini yöneten sınıf.
Kullanıcı girişi (username/password_hash) desteğiyle genişletilmiş versiyon.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any


class DatabaseManager:

    DEFAULT_DB_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "database.db"
    )

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_database(self):
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS athlete (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    name          TEXT    NOT NULL,
                    age           INTEGER,
                    sport         TEXT,
                    username      TEXT    UNIQUE,
                    password_hash TEXT,
                    created_at    TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS session (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    athlete_id    INTEGER NOT NULL REFERENCES athlete(id),
                    date          TEXT    NOT NULL,
                    exercise_type TEXT    NOT NULL,
                    score         REAL    DEFAULT 0,
                    duration_sec  REAL    DEFAULT 0,
                    notes         TEXT
                );

                CREATE TABLE IF NOT EXISTS performance_metric (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id       INTEGER NOT NULL REFERENCES session(id),
                    repetition_count INTEGER DEFAULT 0,
                    average_angle    REAL    DEFAULT 0,
                    stability_score  REAL    DEFAULT 0,
                    symmetry_score   REAL    DEFAULT 0,
                    posture_score    REAL    DEFAULT 0,
                    range_score      REAL    DEFAULT 0,
                    recorded_at      TEXT    DEFAULT (datetime('now'))
                );
            """)
            # Eski tablolara yeni sütunları ekle (migration)
            try:
                conn.execute("ALTER TABLE athlete ADD COLUMN username TEXT UNIQUE")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE athlete ADD COLUMN password_hash TEXT")
            except Exception:
                pass

    # ── Sporcu işlemleri ────────────────────────────────────────────────────

    def create_athlete(self, name: str, age: Optional[int] = None,
                       sport: Optional[str] = None,
                       username: Optional[str] = None,
                       password_hash: Optional[str] = None) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO athlete (name, age, sport, username, password_hash) VALUES (?,?,?,?,?)",
                (name, age, sport, username, password_hash)
            )
            return cursor.lastrowid

    def get_athlete(self, athlete_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM athlete WHERE id = ?", (athlete_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_all_athletes(self) -> List[Dict]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM athlete ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_or_create_athlete(self, name: str, age: Optional[int] = None,
                               sport: Optional[str] = None) -> int:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM athlete WHERE name = ?", (name,)
            ).fetchone()
            if row:
                return row["id"]
        return self.create_athlete(name, age, sport)

    # ── Seans işlemleri ─────────────────────────────────────────────────────

    def create_session(self, athlete_id: int, exercise_type: str,
                       score: float = 0.0, duration_sec: float = 0.0,
                       notes: str = "") -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO session (athlete_id,date,exercise_type,score,duration_sec,notes) VALUES (?,?,?,?,?,?)",
                (athlete_id, now, exercise_type, score, duration_sec, notes)
            )
            return cursor.lastrowid

    def get_sessions_by_athlete(self, athlete_id: int) -> List[Dict]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM session WHERE athlete_id=? ORDER BY date DESC",
                (athlete_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_recent_sessions(self, limit: int = 20) -> List[Dict]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT s.*, a.name as athlete_name FROM session s
                   JOIN athlete a ON s.athlete_id=a.id
                   ORDER BY s.date DESC LIMIT ?""", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def update_session_score(self, session_id: int, score: float, duration_sec: float):
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE session SET score=?, duration_sec=? WHERE id=?",
                (score, duration_sec, session_id)
            )

    # ── Metrik işlemleri ────────────────────────────────────────────────────

    def save_metric(self, session_id: int, rep_count: int, avg_angle: float,
                    stability: float, symmetry: float, posture: float, range_score: float) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO performance_metric
                   (session_id,repetition_count,average_angle,stability_score,
                    symmetry_score,posture_score,range_score) VALUES (?,?,?,?,?,?,?)""",
                (session_id, rep_count, avg_angle, stability, symmetry, posture, range_score)
            )
            return cursor.lastrowid

    def get_metrics_by_session(self, session_id: int) -> List[Dict]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM performance_metric WHERE session_id=? ORDER BY recorded_at",
                (session_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ── İstatistik ──────────────────────────────────────────────────────────

    def get_athlete_stats(self, athlete_id: int) -> Dict[str, Any]:
        with self._get_connection() as conn:
            stats = conn.execute(
                """SELECT COUNT(*) as total_sessions, AVG(score) as average_score,
                          MAX(score) as best_score
                   FROM session WHERE athlete_id=?""", (athlete_id,)
            ).fetchone()
            total_reps_row = conn.execute(
                """SELECT COALESCE(SUM(pm.repetition_count),0) as total_reps
                   FROM performance_metric pm JOIN session s ON pm.session_id=s.id
                   WHERE s.athlete_id=?""", (athlete_id,)
            ).fetchone()
            breakdown = conn.execute(
                """SELECT exercise_type, COUNT(*) as cnt, AVG(score) as avg_score
                   FROM session WHERE athlete_id=? GROUP BY exercise_type""", (athlete_id,)
            ).fetchall()
        return {
            "total_sessions":     stats["total_sessions"] if stats else 0,
            "average_score":      round(stats["average_score"] or 0, 1),
            "best_score":         round(stats["best_score"] or 0, 1),
            "total_reps":         total_reps_row["total_reps"] if total_reps_row else 0,
            "exercise_breakdown": [dict(r) for r in breakdown],
        }

    def get_score_history(self, athlete_id: int, exercise: Optional[str] = None) -> List[Dict]:
        with self._get_connection() as conn:
            if exercise:
                rows = conn.execute(
                    "SELECT date,score,exercise_type FROM session WHERE athlete_id=? AND exercise_type=? ORDER BY date",
                    (athlete_id, exercise)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT date,score,exercise_type FROM session WHERE athlete_id=? ORDER BY date",
                    (athlete_id,)
                ).fetchall()
        return [dict(r) for r in rows]

    def delete_athlete(self, athlete_id: int):
        """Sporcuyu ve tüm seans/metrik verilerini siler."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM performance_metric WHERE session_id IN (SELECT id FROM session WHERE athlete_id=?)", (athlete_id,))
            conn.execute("DELETE FROM session WHERE athlete_id=?", (athlete_id,))
            conn.execute("DELETE FROM athlete WHERE id=?", (athlete_id,))

