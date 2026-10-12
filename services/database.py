
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobagent.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create required tables without deleting existing records."""
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            job_title TEXT NOT NULL,
            job_url TEXT,
            job_description TEXT NOT NULL,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS resume_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            master_resume TEXT NOT NULL,
            jd_analysis TEXT,
            tailored_resume TEXT,
            quality_report TEXT,
            validation_report TEXT,
            status TEXT NOT NULL DEFAULT 'pending_review',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );

        CREATE TABLE IF NOT EXISTS application_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_run_id INTEGER NOT NULL UNIQUE,
            decision TEXT NOT NULL DEFAULT 'pending'
                CHECK (decision IN ('pending', 'approved', 'rejected')),
            decided_at TEXT,
            FOREIGN KEY (resume_run_id) REFERENCES resume_runs(id)
        );

        CREATE TABLE IF NOT EXISTS application_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_run_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'prepared'
                CHECK (status IN ('prepared', 'submitted', 'failed', 'cancelled')),
            submission_attempted INTEGER NOT NULL DEFAULT 0
                CHECK (submission_attempted IN (0, 1)),
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_run_id) REFERENCES resume_runs(id)
        );

        CREATE TABLE IF NOT EXISTS job_match_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            match_score REAL NOT NULL,
            matched_keywords TEXT NOT NULL,
            missing_keywords TEXT NOT NULL,
            resume_fingerprint TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );
        """)


def save_job(
    job_title,
    job_description,
    company=None,
    job_url=None,
    source=None,
):
    if not job_title or not job_title.strip():
        raise ValueError("Job title cannot be empty.")

    if not job_description or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO jobs (
                company, job_title, job_url, job_description, source
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            company,
            job_title.strip(),
            job_url,
            job_description.strip(),
            source,
        ))
        return cursor.lastrowid


def save_resume_run(
    job_id,
    master_resume,
    jd_analysis,
    tailored_resume,
    quality_report,
    validation_report,
):
    """Save workflow results and create a pending approval."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO resume_runs (
                job_id, master_resume, jd_analysis, tailored_resume,
                quality_report, validation_report, status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'pending_review')
        """, (
            job_id,
            master_resume,
            jd_analysis,
            tailored_resume,
            quality_report,
            json.dumps(validation_report, ensure_ascii=False),
        ))

        resume_run_id = cursor.lastrowid

        conn.execute("""
            INSERT INTO application_approvals (
                resume_run_id, decision
            )
            VALUES (?, 'pending')
        """, (resume_run_id,))

        return resume_run_id


def list_jobs():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM jobs ORDER BY id DESC
        """).fetchall()
        return [dict(row) for row in rows]


def list_resume_runs():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                r.id AS resume_run_id,
                r.job_id,
                j.company,
                j.job_title,
                j.job_url,
                r.status,
                r.created_at,
                a.decision
            FROM resume_runs AS r
            JOIN jobs AS j ON j.id = r.job_id
            LEFT JOIN application_approvals AS a
                ON a.resume_run_id = r.id
            ORDER BY r.id DESC
        """).fetchall()
        return [dict(row) for row in rows]


def save_application_attempt(resume_run_id: int, details: str) -> int:
    """Record application preparation only after explicit approval."""
    with get_connection() as conn:
        approval = conn.execute("""
            SELECT a.decision, r.status
            FROM application_approvals AS a
            JOIN resume_runs AS r ON r.id = a.resume_run_id
            WHERE a.resume_run_id = ?
        """, (resume_run_id,)).fetchone()

        if (
            approval is None
            or approval["decision"] != "approved"
            or approval["status"] != "approved_for_submission"
        ):
            raise ValueError(
                "Cannot record an application attempt without approval."
            )

        cursor = conn.execute("""
            INSERT INTO application_attempts (
                resume_run_id, status, submission_attempted, details
            )
            VALUES (?, 'prepared', 0, ?)
        """, (resume_run_id, details))

        return cursor.lastrowid


def list_application_attempts():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                aa.id AS attempt_id,
                aa.resume_run_id,
                aa.status,
                aa.submission_attempted,
                aa.details,
                aa.created_at,
                aa.updated_at,
                j.company,
                j.job_title,
                j.job_url
            FROM application_attempts AS aa
            JOIN resume_runs AS r ON r.id = aa.resume_run_id
            JOIN jobs AS j ON j.id = r.job_id
            ORDER BY aa.id DESC
        """).fetchall()
        return [dict(row) for row in rows]


def save_job_match_results(
    job_id: int,
    match_result: dict,
    resume_fingerprint: str,
) -> int:
    """Persist one job-matching result."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO job_match_results (
                job_id,
                match_score,
                matched_keywords,
                missing_keywords,
                resume_fingerprint
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            job_id,
            float(match_result["match_score"]),
            json.dumps(
                match_result["matched_keywords"],
                ensure_ascii=False,
            ),
            json.dumps(
                match_result["missing_keywords"],
                ensure_ascii=False,
            ),
            resume_fingerprint,
        ))
        return cursor.lastrowid


def list_job_match_results(resume_fingerprint: str | None = None):
    """Retrieve saved matching results, optionally for one resume."""
    with get_connection() as conn:
        query = """
            SELECT
                m.id AS match_id,
                m.job_id,
                j.job_title,
                j.company,
                j.job_url,
                m.match_score,
                m.matched_keywords,
                m.missing_keywords,
                m.resume_fingerprint,
                m.created_at
            FROM job_match_results AS m
            JOIN jobs AS j ON j.id = m.job_id
        """

        if resume_fingerprint:
            rows = conn.execute(
                query + """
                    WHERE m.resume_fingerprint = ?
                    ORDER BY m.match_score DESC, m.id DESC
                """,
                (resume_fingerprint,),
            ).fetchall()
        else:
            rows = conn.execute(
                query + " ORDER BY m.id DESC"
            ).fetchall()

        results = [dict(row) for row in rows]

        for result in results:
            result["matched_keywords"] = json.loads(
                result["matched_keywords"]
            )
            result["missing_keywords"] = json.loads(
                result["missing_keywords"]
            )

        return results


if __name__ == "__main__":
    initialize_database()
    print(f"Database ready: {DB_PATH}")
