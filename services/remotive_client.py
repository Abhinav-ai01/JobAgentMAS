
import json
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from services.database import list_jobs, save_job


API_URL = "https://remotive.com/api/remote-jobs"


class _HTMLTextExtractor(HTMLParser):
    """Convert HTML job descriptions into readable text."""

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self):
        return " ".join(self.parts)


def _clean_description(html):
    parser = _HTMLTextExtractor()
    parser.feed(html or "")
    return parser.get_text()


def fetch_remotive_jobs(search=None, category=None, limit=20):
    """Fetch and normalize remote jobs from Remotive's public API."""
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("limit must be an integer.")

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    params = {"limit": limit}

    if search and search.strip():
        params["search"] = search.strip()

    if category and category.strip():
        params["category"] = category.strip()

    url = f"{API_URL}?{urlencode(params)}"
    request = Request(
        url,
        headers={"User-Agent": "JobAgentMAS/1.0"},
    )

    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(
            f"Remotive API returned HTTP {exc.code}."
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Could not connect to Remotive: {exc.reason}"
        ) from exc
    except (TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Remotive response timed out or contained invalid JSON."
        ) from exc

    normalized = []

    for item in payload.get("jobs", []):
        title = (item.get("title") or "").strip()
        company = (item.get("company_name") or "").strip()
        job_url = (item.get("url") or "").strip()

        if not title or not job_url:
            continue

        description = _clean_description(item.get("description", ""))

        details = [
            f"Source: Remotive",
            f"Original listing: {job_url}",
            f"Category: {item.get('category') or 'Not specified'}",
            f"Job type: {item.get('job_type') or 'Not specified'}",
            (
                "Eligible location: "
                f"{item.get('candidate_required_location') or 'Not specified'}"
            ),
            f"Salary: {item.get('salary') or 'Not specified'}",
            "",
            description,
        ]

        normalized.append({
            "job_title": title,
            "company": company or None,
            "job_url": job_url,
            "job_description": "\n".join(details).strip(),
            "source": "Remotive",
        })

    return normalized


def import_remotive_jobs(search=None, category=None, limit=20):
    """Import fetched listings, skipping URLs already in the job library."""
    fetched = fetch_remotive_jobs(
        search=search,
        category=category,
        limit=limit,
    )

    existing_urls = {
        job.get("job_url")
        for job in list_jobs()
        if job.get("job_url")
    }

    imported = 0
    skipped = 0

    for job in fetched:
        if job["job_url"] in existing_urls:
            skipped += 1
            continue

        save_job(
            job_title=job["job_title"],
            job_description=job["job_description"],
            company=job["company"],
            job_url=job["job_url"],
            source=job["source"],
        )

        existing_urls.add(job["job_url"])
        imported += 1

    return {
        "fetched": len(fetched),
        "imported": imported,
        "skipped_duplicates": skipped,
    }
