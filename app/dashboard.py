
import json
import pandas as pd
import streamlit as st

from services.database import (
    initialize_database,
    list_application_attempts,
    list_job_match_results,
    list_jobs,
    list_resume_runs,
    save_job,
)
from services.matching_service import (
    fingerprint_resume,
    rank_and_save_jobs,
)
from services.approval_service import (
    get_pending_approvals,
    decide_approval,
)
from services.remotive_client import import_remotive_jobs
from agents.leader_agent import run_and_save_job
from agents.application_agent import ApplicationAgent


# ============================================================
# Configuration and helpers
# ============================================================

st.set_page_config(
    page_title="JobAgentMAS",
    page_icon="🎯",
    layout="wide",
)

initialize_database()


def display_value(value, default="Not available"):
    """Return a readable display value."""
    if value is None or value == "":
        return default

    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, ensure_ascii=False)

    return str(value)


def to_dataframe(records):
    """Create a dataframe safely from database records."""
    return pd.DataFrame([dict(record) for record in records])


def show_json(label, value):
    """Display a dictionary, list, or text field."""
    st.markdown(f"**{label}**")

    if value is None or value == "":
        st.info("No data available.")
        return

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            st.json(parsed)
        except (json.JSONDecodeError, TypeError):
            st.text(value)
    elif isinstance(value, (dict, list)):
        st.json(value)
    else:
        st.write(value)


def safe_list(value):
    """Convert a JSON string or list into a list."""
    if isinstance(value, list):
        return value

    if isinstance(value, str):
        try:
            result = json.loads(value)
            if isinstance(result, list):
                return result
        except (json.JSONDecodeError, TypeError):
            pass

    return []


def format_skills(values):
    """Format skill names for readable display."""
    values = safe_list(values)
    return ", ".join(str(item) for item in values) if values else "None detected"


def job_label(job):
    """Create a readable job selector label."""
    title = job.get("job_title", "Untitled job")
    company = job.get("company", "Unknown company")
    return f"{title} — {company} (ID: {job.get('id', '?')})"


def run_status(result):
    """Extract a workflow status from a result dictionary."""
    if not isinstance(result, dict):
        return "unknown"

    return str(result.get("status", "unknown"))


# ============================================================
# Sidebar
# ============================================================

st.sidebar.title("🎯 JobAgentMAS")
st.sidebar.caption("Local Multi-Agent Job Application System")

st.sidebar.markdown("---")
st.sidebar.markdown("### Safety")
st.sidebar.info(
    "Applications must be explicitly approved by you. "
    "Preparing an application does not submit it to an employer."
)

if st.sidebar.button("Refresh database view"):
    st.rerun()


# ============================================================
# Header and navigation
# ============================================================

st.title("🎯 JobAgentMAS")
st.caption(
    "Discover jobs, analyze resume fit, tailor resumes, "
    "review approvals, and track application preparation."
)

tabs = st.tabs([
    "Overview",
    "Job Library",
    "Discover Jobs",
    "Job Matching",
    "Resume Workflow",
    "Approval Queue",
    "Application History",
])


# ============================================================
# 1. Overview
# ============================================================

with tabs[0]:
    st.header("Overview")

    try:
        jobs = list_jobs()
        resume_runs = list_resume_runs()
        attempts = list_application_attempts()
        pending = get_pending_approvals()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Saved Jobs", len(jobs))
        col2.metric("Resume Runs", len(resume_runs))
        col3.metric("Pending Approvals", len(pending))
        col4.metric("Application Records", len(attempts))

        st.divider()

        st.subheader("Recently Added Jobs")

        if jobs:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Job": job.get("job_title"),
                        "Company": job.get("company"),
                        "Source": job.get("source"),
                        "URL": job.get("job_url"),
                    }
                    for job in jobs[:10]
                ]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                "Your job library is empty. Add a job manually "
                "or discover remote jobs in the Discover Jobs tab."
            )

        st.subheader("Recent Resume Runs")

        if resume_runs:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Run ID": run.get("id"),
                        "Job ID": run.get("job_id"),
                        "Status": run.get("status"),
                        "Created": run.get("created_at"),
                    }
                    for run in resume_runs[:10]
                ]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No resume workflow runs yet.")

    except Exception as exc:
        st.error(f"Could not load overview: {exc}")


# ============================================================
# 2. Job Library
# ============================================================

with tabs[1]:
    st.header("📚 Job Library")
    st.write("View saved jobs or add a job manually.")

    with st.expander("Add a Job Manually", expanded=False):
        with st.form("add_job_form"):
            manual_title = st.text_input("Job title")
            manual_company = st.text_input("Company")
            manual_url = st.text_input("Job URL")
            manual_description = st.text_area(
                "Job description",
                height=200,
            )

            manual_source = st.text_input(
                "Source",
                value="manual",
            )

            submitted = st.form_submit_button("Save Job")

        if submitted:
            if not manual_title.strip():
                st.warning("Enter a job title.")
            elif not manual_description.strip():
                st.warning("Enter a job description.")
            else:
                try:
                    job_id = save_job(
                        job_title=manual_title.strip(),
                        company=manual_company.strip() or None,
                        job_url=manual_url.strip() or None,
                        job_description=manual_description.strip(),
                        source=manual_source.strip() or "manual",
                    )

                    st.success(f"Job saved successfully. Job ID: {job_id}")
                    st.rerun()

                except Exception as exc:
                    st.error(f"Could not save job: {exc}")

    st.divider()
    st.subheader("Saved Jobs")

    try:
        jobs = list_jobs()

        if jobs:
            st.dataframe(
                pd.DataFrame([
                    {
                        "ID": job.get("id"),
                        "Job": job.get("job_title"),
                        "Company": job.get("company"),
                        "Source": job.get("source"),
                        "URL": job.get("job_url"),
                    }
                    for job in jobs
                ]),
                use_container_width=True,
                hide_index=True,
            )

            job_options = {
                job_label(job): job
                for job in jobs
            }

            selected_label = st.selectbox(
                "Inspect a job",
                options=list(job_options.keys()),
                key="inspect_job",
            )

            selected_job = job_options[selected_label]

            st.markdown("**Job description**")
            st.write(
                selected_job.get(
                    "job_description",
                    "No description available.",
                )
            )

            if selected_job.get("job_url"):
                st.markdown(
                    f"[Open original job posting]({selected_job['job_url']})"
                )

        else:
            st.info("No jobs have been saved yet.")

    except Exception as exc:
        st.error(f"Could not load jobs: {exc}")


# ============================================================
# 3. Discover Jobs
# ============================================================

with tabs[2]:
    st.header("🌐 Discover Remote Jobs")

    st.write(
        "Search the Remotive remote-jobs source and import "
        "results into your local job library."
    )

    with st.form("remotive_search_form"):
        search_term = st.text_input(
            "Keywords",
            placeholder="Python, backend, data analyst...",
        )

        category = st.selectbox(
            "Category",
            options=[
                "All categories",
                "software-dev",
                "data",
                "devops-sysadmin",
                "product",
                "customer-support",
                "design",
                "marketing",
                "business",
            ],
        )

        import_limit = st.slider(
            "Maximum jobs to import",
            min_value=1,
            max_value=50,
            value=10,
        )

        search_submitted = st.form_submit_button(
            "Discover and Import Jobs"
        )

    if search_submitted:
        try:
            with st.spinner("Searching and importing jobs..."):
                result = import_remotive_jobs(
                    search=search_term.strip() or None,
                    category=(
                        None
                        if category == "All categories"
                        else category
                    ),
                    limit=import_limit,
                )

            st.success("Job discovery request completed.")

            col1, col2, col3 = st.columns(3)
            col1.metric("Fetched", result.get("fetched", 0))
            col2.metric("Imported", result.get("imported", 0))
            col3.metric(
                "Duplicates Skipped",
                result.get("skipped_duplicates", 0),
            )

            st.info(
                "Open Job Library to inspect imported jobs. "
                "Always verify the original listing and its current status."
            )

        except Exception as exc:
            st.error(f"Job discovery failed: {exc}")

    st.divider()
    st.subheader("Current Job Library")

    try:
        jobs = list_jobs()

        if jobs:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Job": job.get("job_title"),
                        "Company": job.get("company"),
                        "Source": job.get("source"),
                        "URL": job.get("job_url"),
                    }
                    for job in jobs
                ]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No jobs saved yet.")

    except Exception as exc:
        st.error(f"Could not load job library: {exc}")


# ============================================================
# 4. Job Matching
# ============================================================

with tabs[3]:
    st.header("🎯 Job Matching")

    st.write(
        "Compare your resume with saved jobs using keyword overlap, "
        "job-title relevance, and explicitly labeled skill requirements. "
        "Scores are heuristic estimates, not official ATS scores."
    )

    resume_for_matching = st.text_area(
        "Paste your master resume",
        height=250,
        key="matching_master_resume",
        placeholder="Paste your complete resume text...",
    )

    if st.button(
        "Rank Jobs Against My Resume",
        key="rank_jobs_button",
    ):
        if not resume_for_matching.strip():
            st.warning("Paste your resume before matching.")

        elif not list_jobs():
            st.warning("Add jobs before running matching.")

        else:
            try:
                with st.spinner("Analyzing and ranking saved jobs..."):
                    ranked = rank_and_save_jobs(
                        resume_for_matching.strip()
                    )

                current_fingerprint = fingerprint_resume(
                    resume_for_matching
                )

                st.session_state["last_match_fingerprint"] = (
                    current_fingerprint
                )
                st.session_state["last_match_results"] = ranked

                st.success(f"Analyzed {len(ranked)} jobs.")

            except Exception as exc:
                st.error(f"Job matching failed: {exc}")

    ranked_results = st.session_state.get(
        "last_match_results",
        [],
    )

    if ranked_results:
        st.subheader("Ranked Job Results")

        overview_rows = []

        for index, item in enumerate(ranked_results):
            overview_rows.append({
                "Rank": index + 1,
                "Job": item.get("job_title", "Unknown"),
                "Company": item.get("company", "Unknown"),
                "Match Score (%)": item.get("match_score", 0),
                "Title Relevance (%)": item.get(
                    "title_relevance_score",
                    0,
                ),
                "Matched Skills": len(
                    item.get("matched_skills", [])
                ),
                "Missing Skills": len(
                    item.get("missing_skills", [])
                ),
                "Missing Must-Have": len(
                    item.get("missing_must_have_skills", [])
                ),
            })

        st.dataframe(
            pd.DataFrame(overview_rows),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "A higher score indicates stronger text-based overlap. "
            "It does not establish eligibility, experience level, "
            "or the likelihood of getting an interview."
        )

        st.subheader("Detailed Skill Analysis")

        for index, item in enumerate(ranked_results):
            title = item.get("job_title", "Untitled job")
            company = item.get("company", "Unknown company")
            score = item.get("match_score", 0)

            with st.expander(
                f"#{index + 1} — {title} | {company} | {score}%"
            ):
                metric1, metric2, metric3 = st.columns(3)

                metric1.metric(
                    "Overall Match",
                    f"{score}%",
                )

                metric2.metric(
                    "Keyword Match",
                    f"{item.get('keyword_score', 0)}%",
                )

                metric3.metric(
                    "Title Relevance",
                    f"{item.get('title_relevance_score', 0)}%",
                )

                st.markdown("**Matched technical skills**")
                matched_skills = item.get("matched_skills", [])

                if matched_skills:
                    st.success(", ".join(matched_skills))
                else:
                    st.info("No recognized skills matched.")

                st.markdown("**Missing recognized skills**")
                missing_skills = item.get("missing_skills", [])

                if missing_skills:
                    st.write(", ".join(missing_skills))
                else:
                    st.write(
                        "No missing skills detected by this matcher."
                    )

                st.markdown("**Must-have requirements**")

                must_have = item.get("must_have_skills", [])
                matched_must = item.get(
                    "matched_must_have_skills",
                    [],
                )
                missing_must = item.get(
                    "missing_must_have_skills",
                    [],
                )

                if must_have:
                    st.write(f"Detected: {', '.join(must_have)}")

                    if matched_must:
                        st.success(
                            f"Matched: {', '.join(matched_must)}"
                        )

                    if missing_must:
                        st.warning(
                            "Not found in resume: "
                            + ", ".join(missing_must)
                        )

                else:
                    st.info(
                        "No clearly labeled must-have skills were "
                        "detected. Review the original job description."
                    )

                st.markdown("**Preferred skills**")

                preferred = item.get("preferred_skills", [])
                matched_preferred = item.get(
                    "matched_preferred_skills",
                    [],
                )
                missing_preferred = item.get(
                    "missing_preferred_skills",
                    [],
                )

                if preferred:
                    st.write(f"Detected: {', '.join(preferred)}")

                    if matched_preferred:
                        st.success(
                            "Matched: " + ", ".join(matched_preferred)
                        )

                    if missing_preferred:
                        st.write(
                            "Not found: "
                            + ", ".join(missing_preferred)
                        )

                else:
                    st.info(
                        "No clearly labeled preferred skills were "
                        "detected."
                    )

                with st.expander("View keyword comparison"):
                    st.write("**Matched keywords**")
                    st.write(
                        ", ".join(item.get("matched_keywords", []))
                        or "None"
                    )

                    st.write("**Missing keywords**")
                    st.write(
                        ", ".join(item.get("missing_keywords", []))
                        or "None"
                    )

                st.caption(
                    item.get(
                        "warning",
                        "This is a heuristic estimate. Verify all "
                        "requirements against the original job description.",
                    )
                )

                if item.get("job_url"):
                    st.markdown(
                        f"[Open original job posting]({item['job_url']})"
                    )

        st.warning(
            "A skill not found in your resume is not necessarily a skill "
            "you lack. Verify the original job description and your actual "
            "qualifications before deciding whether to apply."
        )

    st.divider()
    st.subheader("Saved Match History")

    last_fingerprint = st.session_state.get(
        "last_match_fingerprint"
    )

    try:
        match_history = (
            list_job_match_results(
                resume_fingerprint=last_fingerprint
            )
            if last_fingerprint
            else list_job_match_results()
        )

        if match_history:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Job": item.get("job_title"),
                        "Company": item.get("company"),
                        "Match Score (%)": item.get("match_score"),
                        "Matched Keywords": ", ".join(
                            safe_list(item.get("matched_keywords"))
                        ),
                        "Missing Keywords": ", ".join(
                            safe_list(item.get("missing_keywords"))
                        ),
                        "Created": item.get("created_at"),
                    }
                    for item in match_history
                ]),
                use_container_width=True,
                hide_index=True,
            )

        else:
            st.info("No saved match results yet.")

    except Exception as exc:
        st.error(f"Could not load match history: {exc}")


# ============================================================
# 5. Resume Workflow
# ============================================================

with tabs[4]:
    st.header("📝 Resume Workflow")

    st.write(
        "Analyze a job description and create a tailored resume "
        "for human review."
    )

    try:
        jobs = list_jobs()

        if not jobs:
            st.info(
                "Add or discover a job before starting a resume workflow."
            )

        else:
            job_options = {
                job_label(job): job
                for job in jobs
            }

            selected_job_label = st.selectbox(
                "Choose a saved job",
                options=list(job_options.keys()),
                key="resume_workflow_job",
            )

            selected_job = job_options[selected_job_label]

            st.markdown("**Selected job description**")
            st.write(
                selected_job.get(
                    "job_description",
                    "No description available.",
                )
            )

            master_resume = st.text_area(
                "Paste your master resume",
                height=250,
                key="workflow_master_resume",
                placeholder="Paste your complete resume text...",
            )

            if st.button(
                "Run Resume Workflow",
                key="run_resume_workflow",
            ):
                if not master_resume.strip():
                    st.warning("Paste your resume first.")

                else:
                    try:
                        with st.spinner(
                            "Running the resume analysis workflow..."
                        ):
                            result = run_and_save_job(
                                job_title=selected_job.get("job_title"),
                                job_description=selected_job.get(
                                    "job_description",
                                    "",
                                ),
                                master_resume=master_resume.strip(),
                                company=selected_job.get("company"),
                                job_url=selected_job.get("job_url"),
                                source=selected_job.get("source"),
                            )

                        st.session_state["last_resume_workflow_result"] = (
                            result
                        )

                        st.success(
                            "Resume workflow finished. Review the results "
                            "and use the Approval Queue before preparation."
                        )

                    except Exception as exc:
                        st.error(f"Resume workflow failed: {exc}")

            workflow_result = st.session_state.get(
                "last_resume_workflow_result"
            )

            if workflow_result:
                st.subheader("Latest Workflow Result")

                if isinstance(workflow_result, dict):
                    st.write(
                        "Status:",
                        display_value(
                            workflow_result.get("status", "unknown")
                        ),
                    )

                    for key in (
                        "jd_analysis",
                        "analysis",
                        "tailored_resume",
                        "quality_report",
                        "validation_report",
                        "resume_run_id",
                        "job_id",
                    ):
                        if key in workflow_result:
                            show_json(
                                key.replace("_", " ").title(),
                                workflow_result[key],
                            )

                    with st.expander("View complete workflow output"):
                        st.json(workflow_result)

                else:
                    st.write(workflow_result)

            st.divider()
            st.subheader("Saved Resume Runs")

            resume_runs = list_resume_runs()

            if resume_runs:
                st.dataframe(
                    pd.DataFrame([
                        {
                            "Run ID": run.get("id"),
                            "Job ID": run.get("job_id"),
                            "Status": run.get("status"),
                            "Created": run.get("created_at"),
                        }
                        for run in resume_runs
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )

                run_options = {
                    f"Run {run.get('id')} — "
                    f"Job {run.get('job_id')} — "
                    f"{run.get('status', 'unknown')}": run
                    for run in resume_runs
                }

                selected_run_label = st.selectbox(
                    "Inspect a saved resume run",
                    options=list(run_options.keys()),
                    key="inspect_resume_run",
                )

                selected_run = run_options[selected_run_label]

                with st.expander("View saved run details"):
                    for key, value in selected_run.items():
                        show_json(
                            key.replace("_", " ").title(),
                            value,
                        )

            else:
                st.info("No resume runs saved yet.")

    except Exception as exc:
        st.error(f"Could not load resume workflow: {exc}")


# ============================================================
# 6. Approval Queue
# ============================================================

with tabs[5]:
    st.header("✅ Approval Queue")

    st.write(
        "Review resume runs and explicitly approve or reject them "
        "before any application preparation is allowed."
    )

    try:
        pending_approvals = get_pending_approvals()

        if not pending_approvals:
            st.info("There are no pending approvals.")

        else:
            for approval in pending_approvals:
                run_id = approval.get("resume_run_id")

                if run_id is None:
                    run_id = approval.get("id")

                title = approval.get("job_title", "Unknown job")
                company = approval.get("company", "Unknown company")

                with st.expander(
                    f"Run {run_id} — {title} — {company}"
                ):
                    st.write(
                        "Resume run ID:",
                        display_value(run_id),
                    )

                    for key, value in approval.items():
                        show_json(
                            key.replace("_", " ").title(),
                            value,
                        )

                    if run_id is None:
                        st.error(
                            "This approval record has no identifiable "
                            "resume_run_id. Inspect the database record."
                        )
                        continue

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            "Approve",
                            key=f"approve_{run_id}",
                            type="primary",
                        ):
                            try:
                                decide_approval(
                                    int(run_id),
                                    "approved",
                                )
                                st.success(
                                    f"Run {run_id} approved."
                                )
                                st.rerun()

                            except Exception as exc:
                                st.error(
                                    f"Could not approve run: {exc}"
                                )

                    with col2:
                        if st.button(
                            "Reject",
                            key=f"reject_{run_id}",
                        ):
                            try:
                                decide_approval(
                                    int(run_id),
                                    "rejected",
                                )
                                st.success(
                                    f"Run {run_id} rejected."
                                )
                                st.rerun()

                            except Exception as exc:
                                st.error(
                                    f"Could not reject run: {exc}"
                                )

        st.divider()
        st.subheader("Prepare an Approved Application")

        st.warning(
            "This action prepares a local dry-run record only. "
            "It does not submit an application to an employer."
        )

        resume_runs = list_resume_runs()

        approved_options = {}

        for run in resume_runs:
            if run.get("status") == "approved_for_submission":
                label = (
                    f"Run {run.get('id')} — "
                    f"Job {run.get('job_id')}"
                )
                approved_options[label] = run

        if not approved_options:
            st.info(
                "No resume runs are currently marked "
                "'approved_for_submission'. Approve an eligible run first."
            )

        else:
            selected_approved_label = st.selectbox(
                "Select an approved resume run",
                options=list(approved_options.keys()),
                key="approved_run_selector",
            )

            selected_approved = approved_options[
                selected_approved_label
            ]

            if st.button(
                "Prepare Application (Dry Run)",
                key="prepare_application_button",
            ):
                try:
                    agent = ApplicationAgent()

                    preparation = agent.prepare_application(
                        selected_approved["id"]
                    )

                    st.success(
                        "Dry-run preparation completed. "
                        "No external application was submitted."
                    )

                    show_json(
                        "Preparation result",
                        preparation,
                    )

                except Exception as exc:
                    st.error(
                        f"Could not prepare application: {exc}"
                    )

    except Exception as exc:
        st.error(f"Could not load approval queue: {exc}")


# ============================================================
# 7. Application History
# ============================================================

with tabs[6]:
    st.header("📋 Application History")

    st.write(
        "Review application preparation attempts recorded locally."
    )

    try:
        attempts = list_application_attempts()

        if attempts:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Attempt ID": item.get("id"),
                        "Resume Run ID": item.get("resume_run_id"),
                        "Status": item.get("status"),
                        "Submission Attempted": item.get(
                            "submission_attempted"
                        ),
                        "Created": item.get("created_at"),
                    }
                    for item in attempts
                ]),
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("Attempt Details")

            attempt_options = {
                (
                    f"Attempt {item.get('id')} — "
                    f"Run {item.get('resume_run_id')}"
                ): item
                for item in attempts
            }

            selected_attempt_label = st.selectbox(
                "Select an attempt",
                options=list(attempt_options.keys()),
                key="inspect_application_attempt",
            )

            selected_attempt = attempt_options[
                selected_attempt_label
            ]

            with st.expander("View full attempt record"):
                for key, value in selected_attempt.items():
                    show_json(
                        key.replace("_", " ").title(),
                        value,
                    )

        else:
            st.info(
                "No application attempts have been recorded. "
                "Approved dry-run preparations will appear here."
            )

    except Exception as exc:
        st.error(f"Could not load application history: {exc}")


# ============================================================
# Footer
# ============================================================

st.divider()

st.caption(
    "JobAgentMAS • Local job discovery, resume analysis, "
    "explainable matching, and human-approved application preparation."
)
