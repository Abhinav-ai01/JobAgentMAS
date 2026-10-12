from langchain_ollama import ChatOllama


class ResumeAgent:
    """Tailors resume content to a job description using Ollama."""

    def __init__(self, model: str = "llama3.2:3b"):
        self.llm = ChatOllama(
            model=model,
            temperature=0,
        )

    def tailor_resume(
        self,
        master_resume: str,
        job_description: str,
    ) -> str:
        if not master_resume.strip():
            raise ValueError("Master resume cannot be empty.")

        if not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        prompt = f"""
You are the Resume Agent in a multi-agent job application system.

Tailor the master resume to the supplied job description.

Rules:
- Never invent skills, degrees, employers, or achievements.
- Preserve dates and factual claims.
- Prioritize relevant existing skills and experience.
- Use clear, concise, ATS-friendly wording.
- Include keywords only when supported by the master resume.
- Identify missing skills separately instead of fabricating experience.
- Return the tailored resume as readable plain text.

MASTER RESUME:
{master_resume}

JOB DESCRIPTION:
{job_description}
"""

        response = self.llm.invoke(prompt)
        return response.content


if __name__ == "__main__":
    agent = ResumeAgent()

    sample_resume = """
    Skills: Python, FastAPI, SQL, Git.
    Project: Developed a REST API using Python and FastAPI.
    """

    sample_jd = """
    Python Backend Developer.
    Requirements: Python, FastAPI, REST APIs, SQL, Git, Docker.
    """

    print(agent.tailor_resume(sample_resume, sample_jd))
