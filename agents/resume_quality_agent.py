
from langchain_ollama import ChatOllama


class ResumeQualityAgent:
    """Reviews a tailored resume against the JD and master resume."""

    def __init__(self, model: str = "llama3.2:3b"):
        self.llm = ChatOllama(
            model=model,
            temperature=0,
        )

    def review(
        self,
        master_resume: str,
        job_description: str,
        tailored_resume: str,
    ) -> str:
        if not master_resume.strip():
            raise ValueError("Master resume cannot be empty.")

        if not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        if not tailored_resume.strip():
            raise ValueError("Tailored resume cannot be empty.")

        prompt = f"""
You are the Resume Quality Agent in a multi-agent
job application system.

Review the tailored resume using the source resume
and job description.

Evaluate:
1. Relevant skill and keyword coverage.
2. Alignment with the job requirements.
3. Factual consistency with the master resume.
4. Unsupported claims or invented experience.
5. Readability and ATS-friendly formatting.
6. Genuine missing skills or information.

Rules:
- Never assume a claim is true just because it appears
  in the tailored resume.
- Compare claims against the master resume.
- Identify unsupported claims explicitly.
- Do not treat a missing JD keyword as proof of a skill.
- Do not claim to calculate a validated ATS score.
- Recommend PASS or REVISION REQUIRED.

Return a concise report with:
- Recommendation
- Strengths
- Missing keywords
- Factual concerns
- Suggested improvements

MASTER RESUME:
{master_resume}

JOB DESCRIPTION:
{job_description}

TAILORED RESUME:
{tailored_resume}
"""

        response = self.llm.invoke(prompt)
        return response.content


if __name__ == "__main__":
    agent = ResumeQualityAgent()

    report = agent.review(
        master_resume="""
        Skills: Python, FastAPI, SQL, Git.
        Project: Developed a REST API using Python and FastAPI.
        """,
        job_description="""
        Python Backend Developer.
        Requirements: Python, FastAPI, REST APIs, SQL, Git, Docker.
        """,
        tailored_resume="""
        Python Backend Developer

        Skills: Python, FastAPI, SQL, Git.

        Project: Developed a REST API using Python and FastAPI.
        """,
    )

    print("\n--- RESUME QUALITY REPORT ---\n")
    print(report)
