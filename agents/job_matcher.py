
import re


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for",
    "from", "has", "have", "in", "is", "it", "of", "on", "or",
    "that", "the", "this", "to", "with", "will", "you", "your",
    "our", "we", "they", "their", "experience", "required",
    "requirements", "preferred", "candidate", "role", "work",
    "working", "years", "year", "ability", "strong", "must",
    "should", "would", "could", "including", "include", "using",
    "use", "knowledge", "skills", "skill", "responsibilities",
    "responsibility", "qualifications", "qualification", "about",
    "job", "team", "teams", "company", "looking", "ideal",
    "plus", "nice", "good", "excellent", "proven", "etc",
}

# Common technical skills and technologies.
# This list helps recognize skills, including those written with symbols.
KNOWN_SKILLS = {
    "python", "java", "javascript", "typescript", "c", "c++", "c#",
    "go", "golang", "rust", "ruby", "php", "kotlin", "swift",
    "scala", "r", "matlab", "sql", "nosql", "html", "css",
    "react", "react.js", "angular", "vue", "node.js", "nodejs",
    "next.js", "nextjs", "express", "fastapi", "django", "flask",
    "spring", "spring boot", "dotnet", ".net", "asp.net",
    "rest", "rest api", "graphql", "api", "microservices",
    "postgresql", "postgres", "mysql", "sqlite", "mongodb",
    "redis", "elasticsearch", "firebase", "supabase",
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
    "terraform", "linux", "git", "github", "gitlab", "jenkins",
    "ci/cd", "github actions", "devops", "machine learning",
    "deep learning", "artificial intelligence", "ai", "nlp",
    "pandas", "numpy", "pytorch", "tensorflow", "scikit-learn",
    "langchain", "langgraph", "llm", "rag", "data analysis",
    "data engineering", "data science", "power bi", "tableau",
    "excel", "spark", "hadoop", "airflow", "kafka",
    "pytest", "unit testing", "automation testing", "selenium",
    "playwright", "agile", "scrum", "oop", "data structures",
    "algorithms", "system design", "backend", "frontend",
    "full stack", "full-stack", "software development",
}

MUST_HAVE_LABELS = (
    "must have",
    "must-have",
    "required skills",
    "required qualifications",
    "minimum qualifications",
    "requirements",
    "you will need",
    "what you need",
)

PREFERRED_LABELS = (
    "preferred skills",
    "preferred qualifications",
    "nice to have",
    "nice-to-have",
    "bonus points",
    "bonus skills",
    "desirable skills",
)


def normalize_text(text: str) -> str:
    """Normalize text for comparisons."""
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def extract_keywords(text: str) -> set[str]:
    """Extract normalized words while preserving common technical tokens."""
    normalized = normalize_text(text)

    # Preserve technical expressions that a simple word tokenizer can lose.
    tokens = re.findall(
        r"[a-zA-Z][a-zA-Z0-9]*(?:[.+#/-][a-zA-Z0-9+#.-]+)*"
        r"|[a-zA-Z0-9]+",
        normalized,
    )

    result = set()

    for token in tokens:
        token = token.strip(".,;:!?()[]{}\"'")

        if len(token) > 1 and token not in STOPWORDS:
            result.add(token)

    return result


def extract_known_skills(text: str) -> set[str]:
    """Find recognized skills using whole-phrase boundaries."""
    normalized = normalize_text(text)
    found = set()

    for skill in KNOWN_SKILLS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"

        if re.search(pattern, normalized):
            found.add(skill)

    return found


def _extract_labeled_skills(
    text: str,
    labels: tuple[str, ...],
) -> set[str]:
    """
    Extract recognized skills from explicitly labeled requirement sections.

    Supports headings and inline labels. Because job descriptions vary,
    this is a heuristic and may not identify every requirement correctly.
    """
    lines = (text or "").splitlines()
    selected_parts = []
    collecting_section = False

    heading_pattern = re.compile(
        r"^\s*(?:[-*•]\s*)?("
        + "|".join(re.escape(label) for label in labels)
        + r")\s*[:\-]?\s*(.*)$",
        re.IGNORECASE,
    )

    other_labels = MUST_HAVE_LABELS + PREFERRED_LABELS

    other_heading_pattern = re.compile(
        r"^\s*(?:[-*•]\s*)?("
        + "|".join(re.escape(label) for label in other_labels)
        + r")\s*[:\-]?\s*(.*)$",
        re.IGNORECASE,
    )

    for line in lines:
        stripped = line.strip()

        if not stripped:
            collecting_section = False
            continue

        match = heading_pattern.match(stripped)

        if match:
            collecting_section = True
            remainder = match.group(2).strip()
            if remainder:
                selected_parts.append(remainder)
            continue

        # Stop a section when another explicitly labeled section begins.
        other_match = other_heading_pattern.match(stripped)

        if other_match:
            collecting_section = False
            continue

        # A new plain heading generally ends the previous section.
        if (
            collecting_section
            and len(stripped) < 90
            and stripped.endswith(":")
        ):
            collecting_section = False
            continue

        # Also recognize inline labels such as "Must-have skills: Python".
        lowered = stripped.lower()

        for label in labels:
            inline_pattern = re.compile(
                re.escape(label) + r"\s*:\s*(.+)",
                re.IGNORECASE,
            )
            inline_match = inline_pattern.search(stripped)

            if inline_match:
                selected_parts.append(inline_match.group(1))
                break
        else:
            if collecting_section:
                selected_parts.append(stripped)

    return extract_known_skills(" ".join(selected_parts))


def _ratio(matched_count: int, total_count: int) -> float:
    """Return a percentage, safely handling empty collections."""
    if total_count == 0:
        return 0.0

    return round(100.0 * matched_count / total_count, 2)


class JobMatcherAgent:
    """
    Rank jobs using explainable keyword, title, and requirement matching.

    Scores are heuristic indicators, not official ATS scores or proof
    that a candidate is qualified for a job.
    """

    def match_job(
        self,
        master_resume: str,
        job_description: str,
        job_title: str = "",
    ) -> dict:
        if not master_resume or not master_resume.strip():
            raise ValueError("Master resume cannot be empty.")

        resume_keywords = extract_keywords(master_resume)
        job_keywords = extract_keywords(job_description)

        matched_keywords = sorted(resume_keywords & job_keywords)
        missing_keywords = sorted(job_keywords - resume_keywords)

        keyword_score = _ratio(
            len(matched_keywords),
            len(job_keywords),
        )

        # Title relevance measures overlap with meaningful title words.
        title_keywords = extract_keywords(job_title)
        matched_title_keywords = sorted(
            title_keywords & resume_keywords
        )
        title_score = _ratio(
            len(matched_title_keywords),
            len(title_keywords),
        )

        resume_skills = extract_known_skills(master_resume)
        job_skills = extract_known_skills(job_description)

        matched_skills = sorted(resume_skills & job_skills)
        missing_skills = sorted(job_skills - resume_skills)

        must_have_skills = _extract_labeled_skills(
            job_description,
            MUST_HAVE_LABELS,
        )
        preferred_skills = _extract_labeled_skills(
            job_description,
            PREFERRED_LABELS,
        )

        matched_must_have = sorted(
            must_have_skills & resume_skills
        )
        missing_must_have = sorted(
            must_have_skills - resume_skills
        )

        matched_preferred = sorted(
            preferred_skills & resume_skills
        )
        missing_preferred = sorted(
            preferred_skills - resume_skills
        )

        if must_have_skills:
            must_have_score = _ratio(
                len(matched_must_have),
                len(must_have_skills),
            )

            score = (
                0.55 * keyword_score
                + 0.20 * title_score
                + 0.25 * must_have_score
            )
        else:
            # Do not penalize jobs simply because they lack labeled
            # requirements. Title relevance remains a smaller signal.
            score = 0.80 * keyword_score + 0.20 * title_score

        score = round(max(0.0, min(100.0, score)), 2)

        return {
            "match_score": score,
            "keyword_score": keyword_score,
            "title_relevance_score": title_score,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "must_have_skills": sorted(must_have_skills),
            "matched_must_have_skills": matched_must_have,
            "missing_must_have_skills": missing_must_have,
            "preferred_skills": sorted(preferred_skills),
            "matched_preferred_skills": matched_preferred,
            "missing_preferred_skills": missing_preferred,
            "human_review_required": True,
            "warning": (
                "This is an explainable heuristic, not an official ATS "
                "score or a measure of actual qualification. Job descriptions "
                "may be ambiguous, and requirements need human review."
            ),
        }

    def rank_jobs(
        self,
        master_resume: str,
        jobs: list[dict],
    ) -> list[dict]:
        """Return jobs sorted by descending match score."""
        if not master_resume or not master_resume.strip():
            raise ValueError("Master resume cannot be empty.")

        ranked = []

        for job in jobs:
            result = self.match_job(
                master_resume=master_resume,
                job_description=job.get("job_description", ""),
                job_title=job.get("job_title", ""),
            )

            ranked.append({
                **job,
                **result,
            })

        return sorted(
            ranked,
            key=lambda job: job["match_score"],
            reverse=True,
        )


if __name__ == "__main__":
    resume = (
        "Python developer with FastAPI, SQL, REST API, "
        "Git and backend development experience."
    )

    jobs = [
        {
            "job_title": "Python Backend Developer",
            "job_description": (
                "Required skills: Python, FastAPI, SQL, Git. "
                "Preferred skills: Docker, Kubernetes."
            ),
        },
        {
            "job_title": "Frontend Developer",
            "job_description": (
                "Required skills: React, CSS, HTML, JavaScript."
            ),
        },
    ]

    matcher = JobMatcherAgent()

    for job in matcher.rank_jobs(resume, jobs):
        print(f"\n{job['job_title']}: {job['match_score']}%")
        print("Matched skills:", job["matched_skills"])
        print("Missing skills:", job["missing_skills"])
        print("Missing must-have:", job["missing_must_have_skills"])
        print("Missing preferred:", job["missing_preferred_skills"])
