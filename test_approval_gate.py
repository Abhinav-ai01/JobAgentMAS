
from services.approval_service import (
    get_pending_approvals,
    get_approved_for_submission,
)

pending = get_pending_approvals()
approved = get_approved_for_submission()

print("Pending approvals:", len(pending))
print("Approved for submission:", len(approved))

for item in approved:
    print(
        item["resume_run_id"],
        item["company"],
        item["job_title"],
        item["decision"],
    )

assert all(item["decision"] == "approved" for item in approved)
assert all(
    item["status"] == "approved_for_submission"
    for item in approved
)

print("Approval gate test passed.")
