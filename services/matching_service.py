
import hashlib

from agents.job_matcher import JobMatcherAgent
from services.database import (
    list_jobs,
    save_job_match_results,
)


def fingerprint_resume(master_resume: str) -> str:
    """Create a non-reversible identifier for a resume's contents."""
    return hashlib.sha256(
        master_resume.strip().encode("utf-8")
    ).hexdigest()


def rank_and_save_jobs(master_resume: str) -> list[dict]:
    """Rank saved jobs and persist their match results."""
    if not master_resume.strip():
        raise ValueError("Master resume cannot be empty.")

    jobs = list_jobs()
    matcher = JobMatcherAgent()
    fingerprint = fingerprint_resume(master_resume)

    ranked_jobs = matcher.rank_jobs(master_resume, jobs)

    for job in ranked_jobs:
        save_job_match_results(
            job_id=job["id"],
            match_result=job,
            resume_fingerprint=fingerprint,
        )

    return ranked_jobs
