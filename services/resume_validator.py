
import re


def normalize(text: str) -> str:
    """Normalize text for simple keyword and phrase matching."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def validate_resume(
    master_resume: str,
    job_description: str,
    tailored_resume: str,
) -> dict:
    """Run basic deterministic checks on resume content."""

    if not master_resume.strip():
        raise ValueError("Master resume cannot be empty.")

    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    if not tailored_resume.strip():
        raise ValueError("Tailored resume cannot be empty.")

    master = normalize(master_resume)
    jd = normalize(job_description)
    tailored = normalize(tailored_resume)

    # Important JD terms to inspect. These are examples, not
    # a universal skills dictionary.
    keywords = [
        "python",
        "fastapi",
        "rest api",
        "sql",
        "git",
        "docker",
    ]

    matched_keywords = [
        keyword for keyword in keywords
        if keyword in jd and keyword in tailored
    ]

    missing_keywords = [
        keyword for keyword in keywords
        if keyword in jd and keyword not in tailored
    ]

    # Flag skill keywords in the tailored resume that do not
    # appear in the master resume. This is a warning for review,
    # not proof that a claim is false.
    unsupported_skill_keywords = [
        keyword for keyword in keywords
        if keyword in tailored and keyword not in master
    ]

    return {
        "keyword_coverage": (
            round(len(matched_keywords) / len(matched_keywords + missing_keywords) * 100)
            if matched_keywords or missing_keywords
            else 0
        ),
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "unsupported_skill_keywords": unsupported_skill_keywords,
        "human_review_required": bool(
            missing_keywords or unsupported_skill_keywords
        ),
    }


if __name__ == "__main__":
    master = """
    Skills: Python, FastAPI, SQL, Git.
    Project: Developed a REST API using Python and FastAPI.
    """

    jd = """
    Python Backend Developer.
    Requirements: Python, FastAPI, REST API, SQL, Git, Docker.
    """

    tailored = """
    Skills: Python, FastAPI, SQL, Git.
    Project: Developed a REST API using Python and FastAPI.
    """

    print(validate_resume(master, jd, tailored))
