
from langchain_ollama import ChatOllama


class JDAnalyzerAgent:
    """Analyzes a job description using a local Ollama model."""

    def __init__(self, model: str = "llama3.2:3b"):
        self.llm = ChatOllama(
            model=model,
            temperature=0,
        )

    def analyze(self, job_description: str) -> str:
        if not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        prompt = f"""
You are the Job Description Analyzer Agent in a multi-agent
job application system.

Analyze the job description below and report:
1. Job title and likely responsibilities.
2. Required technical skills.
3. Preferred skills.
4. Experience and education requirements.
5. Important ATS keywords.

Do not invent requirements that are not supported by the text.
Mark information as "Not specified" when necessary.

JOB DESCRIPTION:
{job_description}
"""
        response = self.llm.invoke(prompt)
        return response.content


if __name__ == "__main__":
    agent = JDAnalyzerAgent()

    sample_jd = """
    Python Backend Developer

    Requirements:
    - Python and FastAPI
    - REST API development
    - SQL databases
    - Git
    - Familiarity with Docker
    """

    result = agent.analyze(sample_jd)
    print("\n--- JOB DESCRIPTION ANALYSIS ---\n")
    print(result)
