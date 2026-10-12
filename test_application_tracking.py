from services.database import (
    initialize_database,
    list_application_attempts,
)
from agents.application_agent import ApplicationAgent

initialize_database()

agent = ApplicationAgent()
results = agent.run_dry_run()

print("\nSaved application attempts:")

attempts = list_application_attempts()

for attempt in attempts:
    print(
        {
            "attempt_id": attempt["attempt_id"],
            "resume_run_id": attempt["resume_run_id"],
            "company": attempt["company"],
            "job_title": attempt["job_title"],
            "status": attempt["status"],
            "submission_attempted": attempt["submission_attempted"],
        }
    )

assert all(
    attempt["submission_attempted"] == 0
    for attempt in attempts
)

print("\nApplication tracking check passed.")
