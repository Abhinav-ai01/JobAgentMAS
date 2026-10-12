
from services.database import get_connection


def get_pending_approvals() -> list[dict]:
    """Return resumes waiting for human review."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                r.id AS resume_run_id,
                r.jd_analysis,
                r.tailored_resume,
                r.quality_report,
                r.validation_report,
                r.status,
                j.company,
                j.job_title,
                j.job_description,
                j.job_url,
                a.decision
            FROM resume_runs r
            JOIN jobs j ON j.id = r.job_id
            JOIN application_approvals a
                ON a.resume_run_id = r.id
            WHERE a.decision = 'pending'
            ORDER BY r.id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def decide_approval(resume_run_id: int, decision: str) -> None:
    """Record a human decision; never submit an application."""
    if decision not in {"approved", "rejected"}:
        raise ValueError("Decision must be approved or rejected.")

    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE application_approvals
            SET decision = ?,
                decided_at = CURRENT_TIMESTAMP
            WHERE resume_run_id = ?
              AND decision = 'pending'
        """, (decision, resume_run_id))

        if cursor.rowcount != 1:
            raise ValueError(
                "Pending approval not found, or a decision was already recorded."
            )

        status = (
            "approved_for_submission"
            if decision == "approved"
            else "rejected"
        )

        conn.execute("""
            UPDATE resume_runs
            SET status = ?
            WHERE id = ?
        """, (status, resume_run_id))


def get_approved_for_submission() -> list[dict]:
    """Return only resume runs explicitly approved by the user."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                r.id AS resume_run_id,
                r.tailored_resume,
                r.validation_report,
                r.status,
                j.company,
                j.job_title,
                j.job_url,
                a.decision
            FROM resume_runs r
            JOIN jobs j ON j.id = r.job_id
            JOIN application_approvals a
                ON a.resume_run_id = r.id
            WHERE a.decision = 'approved'
              AND r.status = 'approved_for_submission'
            ORDER BY r.id DESC
        """).fetchall()

        return [dict(row) for row in rows]



if __name__ == "__main__":
    pending = get_pending_approvals()

    print(f"Pending approvals: {len(pending)}")

    for item in pending:
        print(
            item["resume_run_id"],
            item["company"],
            item["job_title"],
            item["decision"],
        )
