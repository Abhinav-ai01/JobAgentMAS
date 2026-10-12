import pytest

import services.database as database
from services.approval_service import (
    decide_approval,
    get_approved_for_submission,
)
from agents.application_agent import ApplicationAgent


@pytest.fixture
def prepared_resume(tmp_path, monkeypatch):
    """Create an isolated database with one pending resume."""
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "test_jobagent.db",
    )

    database.initialize_database()

    job_id = database.save_job(
        job_title="Python Backend Developer",
        job_description="Python, FastAPI, SQL",
        company="Test Company",
        job_url="https://example.com/job",
        source="automated_test",
    )

    resume_run_id = database.save_resume_run(
        job_id=job_id,
        master_resume="Skills: Python, FastAPI, SQL.",
        jd_analysis="Required skills: Python, FastAPI, SQL.",
        tailored_resume="Python Backend Developer resume.",
        quality_report="Quality review completed.",
        validation_report={
            "human_review_required": True,
            "unsupported_skill_keywords": [],
        },
    )

    return resume_run_id


def test_pending_resume_cannot_be_prepared(prepared_resume):
    """A pending resume must not enter application preparation."""
    agent = ApplicationAgent()

    with pytest.raises(ValueError, match="not approved"):
        agent.prepare_application(prepared_resume)

    assert database.list_application_attempts() == []


def test_rejected_resume_cannot_be_prepared(prepared_resume):
    """A rejected resume must remain blocked."""
    decide_approval(prepared_resume, "rejected")

    agent = ApplicationAgent()

    with pytest.raises(ValueError, match="not approved"):
        agent.prepare_application(prepared_resume)

    assert database.list_application_attempts() == []


def test_approved_resume_can_be_prepared(prepared_resume):
    """An approved resume can be prepared in dry-run mode."""
    decide_approval(prepared_resume, "approved")

    approved = get_approved_for_submission()

    assert len(approved) == 1
    assert approved[0]["resume_run_id"] == prepared_resume

    agent = ApplicationAgent()
    result = agent.prepare_application(prepared_resume)

    assert result["status"] == "dry_run_ready"
    assert result["submission_attempted"] is False

    attempts = database.list_application_attempts()

    assert len(attempts) == 1
    assert attempts[0]["resume_run_id"] == prepared_resume
    assert attempts[0]["status"] == "prepared"
    assert attempts[0]["submission_attempted"] == 0
