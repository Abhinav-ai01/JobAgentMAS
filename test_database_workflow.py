
from agents.leader_agent import run_and_save_job
from services.database import initialize_database, list_resume_runs


initialize_database()

result = run_and_save_job(
    job_title="Python Backend Developer",
    company="Demo Company",
    job_url="https://example.com/jobs/demo",
    source="manual_test",
    job_description="""
    Requirements: Python, FastAPI, REST APIs, SQL, Git, Docker.
    """,
    master_resume="""
    Skills: Python, FastAPI, SQL, Git.
    Project: Developed a REST API using Python and FastAPI.
    """,
)

print("Workflow status:", result["status"])
print("Job ID:", result.get("job_id"))
print("Resume run ID:", result.get("resume_run_id"))
print("Approval status:", result.get("approval_status"))
print("\nSaved records:")
print(list_resume_runs())
