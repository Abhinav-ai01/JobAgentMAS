import pytest

import services.database as database
from services.matching_service import (
    fingerprint_resume,
    rank_and_save_jobs,
)


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    """Use a temporary SQLite database for every test."""
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "test_jobagent.db",
    )

    database.initialize_database()

    database.save_job(
        job_title="Python Backend Developer",
        company="Backend Company",
        job_url="https://example.com/backend",
        job_description="Python FastAPI SQL Git backend development",
        source="automated_test",
    )

    database.save_job(
        job_title="Frontend Developer",
        company="Frontend Company",
        job_url="https://example.com/frontend",
        job_description="React CSS HTML JavaScript frontend development",
        source="automated_test",
    )


def test_matching_ranks_relevant_job_first(isolated_database):
    """A relevant backend job should rank above the frontend job."""
    resume = "Python FastAPI SQL Git backend developer"

    ranked = rank_and_save_jobs(resume)

    assert len(ranked) == 2
    assert ranked[0]["job_title"] == "Python Backend Developer"
    assert ranked[0]["match_score"] > ranked[1]["match_score"]


def test_matching_results_are_saved(isolated_database):
    """Matching results should persist in SQLite."""
    resume = "Python FastAPI SQL Git backend developer"

    rank_and_save_jobs(resume)

    history = database.list_job_match_results(
        fingerprint_resume(resume)
    )

    assert len(history) == 2

    titles = {item["job_title"] for item in history}

    assert titles == {
        "Python Backend Developer",
        "Frontend Developer",
    }

    for item in history:
        assert isinstance(item["matched_keywords"], list)
        assert isinstance(item["missing_keywords"], list)
        assert item["resume_fingerprint"] == fingerprint_resume(resume)


def test_empty_resume_is_rejected(isolated_database):
    """An empty resume must not produce match results."""
    with pytest.raises(ValueError, match="Master resume cannot be empty"):
        rank_and_save_jobs("   ")

    assert database.list_job_match_results() == []


def test_resume_fingerprint_is_deterministic():
    """The same normalized resume should produce the same fingerprint."""
    first = fingerprint_resume("  Python developer  ")
    second = fingerprint_resume("Python developer")

    assert first == second
