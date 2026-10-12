from services.database import (
    initialize_database,
    save_job,
    save_resume_run,
)


from typing import TypedDict


from langgraph.graph import END, START, StateGraph

from agents.jd_analyzer import JDAnalyzerAgent
from agents.resume_agent import ResumeAgent
from agents.resume_quality_agent import ResumeQualityAgent
from services.resume_validator import validate_resume


class JobState(TypedDict, total=False):
    job_description: str
    master_resume: str
    jd_analysis: str
    tailored_resume: str
    quality_report: str
    validation_report: dict
    status: str
    error: str


def analyze_job(state: JobState) -> JobState:
    agent = JDAnalyzerAgent()
    return {
        "jd_analysis": agent.analyze(state["job_description"])
    }


def tailor_resume(state: JobState) -> JobState:
    agent = ResumeAgent()
    return {
        "tailored_resume": agent.tailor_resume(
            master_resume=state["master_resume"],
            job_description=state["job_description"],
        )
    }


def review_resume(state: JobState) -> JobState:
    agent = ResumeQualityAgent()
    return {
        "quality_report": agent.review(
            master_resume=state["master_resume"],
            job_description=state["job_description"],
            tailored_resume=state["tailored_resume"],
        )
    }


def validate_generated_resume(state: JobState) -> JobState:
    report = validate_resume(
        master_resume=state["master_resume"],
        job_description=state["job_description"],
        tailored_resume=state["tailored_resume"],
    )
    return {"validation_report": report}


def build_workflow():
    graph = StateGraph(JobState)

    graph.add_node("jd_analyzer", analyze_job)
    graph.add_node("resume_agent", tailor_resume)
    graph.add_node("resume_quality", review_resume)
    graph.add_node("resume_validator", validate_generated_resume)

    graph.add_edge(START, "jd_analyzer")
    graph.add_edge("jd_analyzer", "resume_agent")
    graph.add_edge("resume_agent", "resume_quality")
    graph.add_edge("resume_quality", "resume_validator")
    graph.add_edge("resume_validator", END)

    return graph.compile()


def run_job_workflow(
    job_description: str,
    master_resume: str,
) -> JobState:
    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    if not master_resume.strip():
        raise ValueError("Master resume cannot be empty.")

    try:
        result = build_workflow().invoke({
            "job_description": job_description,
            "master_resume": master_resume,
            "status": "started",
        })
        result["status"] = "completed"
        return result

    except Exception as exc:
        return {
            "job_description": job_description,
            "master_resume": master_resume,
            "status": "failed",
            "error": str(exc),
        }

def run_and_save_job(
    job_title: str,
    job_description: str,
    master_resume: str,
    company: str | None = None,
    job_url: str | None = None,
    source: str | None = None,
) -> dict:
    """Run all agents and persist their results for human review."""

    initialize_database()

    result = run_job_workflow(
        job_description=job_description,
        master_resume=master_resume,
    )

    if result["status"] != "completed":
        return result

    job_id = save_job(
        job_title=job_title,
        job_description=job_description,
        company=company,
        job_url=job_url,
        source=source,
    )

    resume_run_id = save_resume_run(
        job_id=job_id,
        master_resume=master_resume,
        jd_analysis=result.get("jd_analysis", ""),
        tailored_resume=result.get("tailored_resume", ""),
        quality_report=result.get("quality_report", ""),
        validation_report=result.get("validation_report", {}),
    )

    result["job_id"] = job_id
    result["resume_run_id"] = resume_run_id
    result["approval_status"] = "pending"

    return result

if __name__ == "__main__":
    result = run_job_workflow(
        job_description="""
        Python Backend Developer

        Requirements:
        - Python and FastAPI
        - REST API development
        - SQL databases
        - Git
        - Docker
        """,
        master_resume="""
        Skills: Python, FastAPI, SQL, Git.

        Project:
        Developed a REST API using Python and FastAPI.
        """,
    )

    print("\n========== LEADER AGENT REPORT ==========")
    print("Status:", result["status"])

    if result.get("jd_analysis"):
        print("\n========== JOB DESCRIPTION ANALYSIS ==========")
        print(result["jd_analysis"])

    if result.get("tailored_resume"):
        print("\n========== TAILORED RESUME ==========")
        print(result["tailored_resume"])

    if result.get("quality_report"):
        print("\n========== AI QUALITY REVIEW ==========")
        print(result["quality_report"])

    if result.get("validation_report"):
        print("\n========== RULE-BASED VALIDATION ==========")
        for key, value in result["validation_report"].items():
            print(f"{key}: {value}")

    if result.get("error"):
        print("\n========== ERROR ==========")
        print(result["error"])
