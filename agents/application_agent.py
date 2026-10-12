import json

from services.approval_service import get_approved_for_submission
from services.database import save_application_attempt


class ApplicationAgent:
    """
    Prepares applications for explicitly approved resumes.

    This version operates in dry-run mode only.
    It never submits applications to external platforms.
    """

    def prepare_application(self, resume_run_id: int) -> dict:
        approved_items = get_approved_for_submission()

        approved_item = next(
            (
                item
                for item in approved_items
                if item["resume_run_id"] == resume_run_id
            ),
            None,
        )

        if approved_item is None:
            raise ValueError(
                f"Resume run {resume_run_id} is not approved "
                "for submission."
            )

        application = {
            "status": "dry_run_ready",
            "resume_run_id": approved_item["resume_run_id"],
            "company": approved_item["company"],
            "job_title": approved_item["job_title"],
            "job_url": approved_item["job_url"],
            "tailored_resume": approved_item["tailored_resume"],
            "validation_report": approved_item["validation_report"],
            "submission_attempted": False,
            "message": (
                "Application prepared in dry-run mode. "
                "Nothing was submitted externally."
            ),
        }

        # Record the preparation in the database.
        attempt_id = save_application_attempt(
            resume_run_id=resume_run_id,
            details=json.dumps(application, ensure_ascii=False),
        )

        application["attempt_id"] = attempt_id

        return application

    def run_dry_run(self) -> list[dict]:
        """Prepare and record all currently approved resumes."""
        approved_items = get_approved_for_submission()

        if not approved_items:
            print("No approved resumes are available.")
            return []

        results = []

        for item in approved_items:
            try:
                application = self.prepare_application(
                    item["resume_run_id"]
                )
                results.append(application)

                print("-" * 50)
                print("Mode: DRY RUN")
                print("Attempt ID:", application["attempt_id"])
                print("Resume run ID:", application["resume_run_id"])
                print("Company:", application["company"])
                print("Job title:", application["job_title"])
                print("Job URL:", application["job_url"])
                print("Submission attempted: False")
                print("Status: Prepared and recorded")

            except Exception as exc:
                print(
                    f"Could not prepare resume run "
                    f"{item['resume_run_id']}: {exc}"
                )

        return results


if __name__ == "__main__":
    agent = ApplicationAgent()
    agent.run_dry_run()
