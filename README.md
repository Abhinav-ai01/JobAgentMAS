# JobAgentMAS — Multi-Agent Job Application System

**An AI-powered job application assistant built with Python, LangGraph, Ollama, SQLite, and Streamlit.**

JobAgentMAS is a local-first project designed to streamline job discovery, resume analysis, job matching, skill-gap identification, and application preparation through an interactive dashboard and a multi-agent workflow.

The system combines local language-model inference with structured job data, explainable matching results, persistent storage, and human-in-the-loop approval controls.

**Developer:** Abhinav  
**Repository:** [github.com/abhinav-ai01/JobAgentMAS](https://github.com/abhinav-ai01/JobAgentMAS)

---

## Key Features

- **Remote Job Discovery:** Fetch remote job listings from the Remotive API and save them to a local database.
- **Job Management:** Store, inspect, and manage job descriptions, companies, source information, and posting URLs.
- **AI-Assisted Resume Analysis:** Analyze job descriptions and support resume tailoring through a multi-step workflow.
- **Local LLM Integration:** Use Ollama with the `llama3.2:3b` model for supported language-model tasks.
- **Explainable Job Matching:** Compare resume content with job descriptions using keyword overlap and recognized technical skills.
- **Skill-Gap Identification:** Highlight skills mentioned in job descriptions that are not found in the supplied resume text.
- **Weighted Matching:** Combine keyword relevance, job-title relevance, and explicitly labeled must-have requirements.
- **Streamlit Dashboard:** Manage job discovery, matching, resume workflows, approvals, and application-preparation records.
- **SQLite Persistence:** Store jobs, resume runs, match results, and application-related records locally.
- **Human-in-the-Loop Approval:** Require an explicit approval decision before an eligible application can be prepared.
- **Automated Tests:** Test approval safeguards, job ranking, database persistence, and resume fingerprinting.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Core application logic |
| LangGraph | Workflow orchestration |
| Ollama | Local LLM runtime |
| Llama 3.2 3B | Configured local language model |
| Streamlit | Interactive web dashboard |
| SQLite | Persistent local database |
| pandas | Tabular data presentation |
| pytest | Automated testing |
| Remotive API | Remote job discovery |

## Architecture

```text
                 Remotive API
                      |
                      v
               Job Discovery
                      |
                      v
                 SQLite DB
                      |
             +--------+--------+
             |                 |
             v                 v
       Job Matching      Resume Workflow
             |                 |
             v                 v
       Match Scoring     JD Analysis
             |                 |
             v                 v
       Skill-Gap Data    Resume Tailoring
                               |
                               v
                       Resume Validation
                               |
                               v
                        Human Approval
                               |
                               v
                     Application Preparation
                           (Dry Run)

              Streamlit Dashboard
          Provides the user interface
```

The diagram represents the intended high-level workflow. The exact stages and outputs depend on the implemented agents and workflow configuration.

## Project Structure

```text
JobAgentMAS/
├── agents/
│   ├── application_agent.py
│   ├── jd_analyzer.py
│   ├── job_matcher.py
│   ├── leader_agent.py
│   ├── resume_agent.py
│   └── resume_quality_agent.py
├── app/
│   └── dashboard.py
├── services/
│   ├── approval_service.py
│   ├── database.py
│   ├── matching_service.py
│   ├── remotive_client.py
│   └── resume_validator.py
├── tests/
│   ├── test_approval_safety.py
│   └── test_matching_service.py
├── data/
│   ├── jobs.csv
│   └── .gitkeep
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Setup

### Prerequisites

- Windows 10 or Windows 11
- Python 3.12
- Git
- Ollama installed locally
- An internet connection for installing dependencies and discovering remote jobs

### 1. Clone the repository

```powershell
git clone https://github.com/abhinav-ai01/JobAgentMAS.git
cd JobAgentMAS
```

### 2. Create a virtual environment

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
```

If PowerShell blocks environment activation, run the following in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv312\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install and configure the local model

Install Ollama from [ollama.com](https://ollama.com/).

Download the model:

```powershell
ollama pull llama3.2:3b
```

Verify that it is available:

```powershell
ollama list
```

Ensure Ollama is running before starting workflows that require the model.

### 5. Launch the dashboard

From the project root, execute:

```powershell
python -m streamlit run app/dashboard.py
```

Open the local URL displayed in the terminal, usually:

[http://localhost:8501](http://localhost:8501)

## Using JobAgentMAS

1. **Discover jobs:** Search remote listings or add jobs manually.
2. **Inspect job descriptions:** Review saved descriptions and original posting URLs.
3. **Match your resume:** Paste your master resume and rank saved jobs.
4. **Review skill gaps:** Inspect matching skills, missing keywords, and detected requirements.
5. **Run the resume workflow:** Select a job and provide your resume for analysis and tailoring.
6. **Review the results:** Check the generated content for accuracy and relevance.
7. **Manage approvals:** Explicitly approve or reject eligible resume runs.
8. **Prepare an application:** Create a local dry-run record for an approved resume run.
9. **Review history:** Inspect saved match results and application-preparation records.

## Running Tests

Run the complete test suite:

```powershell
python -m pytest -v
```

Run job-matching tests:

```powershell
python -m pytest tests/test_matching_service.py -v
```

Run approval-safety tests:

```powershell
python -m pytest tests/test_approval_safety.py -v
```

### Verified test results

The project's test suite previously completed with **7 tests passed**:

- 3 approval-safety tests
- 4 job-matching and persistence tests

These results represent the tested code at that point in development. Rerun the tests after subsequent changes to confirm the current state.

## Job-Matching Methodology

The matcher uses transparent text-based heuristics rather than a proprietary ATS algorithm.

Its matching features include:

- Keyword overlap between the resume and job description
- Recognition of common technical skills and technologies
- Job-title relevance
- Detection of explicitly labeled must-have and preferred skills
- Identification of potentially missing skills

The weighted score is a ranking aid, not a probability of being hired or an official ATS score. Requirement extraction depends on how each job description is written, and the results require human review.

## Safety and Privacy

JobAgentMAS incorporates a human approval step before eligible application-preparation actions.

- Pending or rejected resume runs must not be prepared as approved applications.
- Preparation creates a local dry-run record.
- The current workflow does not automatically submit applications to employers.
- Generated resume content should be reviewed before it is shared.
- Local databases, virtual environments, credentials, and private resume files should not be committed to a public repository.

Ollama can run the configured language model locally, while remote job discovery requires an external API connection. Do not assume that every part of the application operates offline.

## Current Limitations

- Matching scores are heuristic and may not reflect actual qualifications.
- Skill extraction is limited by the configured vocabulary and text patterns.
- Job listings may become outdated or unavailable.
- Generated resume content can contain errors and requires verification.
- The project is a development-stage system and should not be considered production-ready without further integration testing.

## Future Improvements

- Semantic job matching using text embeddings
- More robust extraction of mandatory and preferred qualifications
- Persistent storage of detailed skill-match explanations
- Resume export to PDF and DOCX
- Additional job-board integrations
- More end-to-end and integration tests
- Improved logging, error handling, and evaluation metrics
- Optional external application integrations with explicit user confirmation

## Author

**Abhinav**

GitHub: [@abhinav-ai01](https://github.com/abhinav-ai01)

---

*Built to explore local LLMs, agentic workflows, explainable job matching, resume automation, and human-in-the-loop AI systems.*
