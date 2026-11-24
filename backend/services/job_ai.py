from pydantic import BaseModel, Field

from services.gemini_client import generate_structured


class StructuredJob(BaseModel):
    job_title: str | None = None
    company: str | None = None

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    education_requirements: list[str] = Field(default_factory=list)
    experience_requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)


def build_prompt(job_description: str) -> str:
    return f"""
You are a professional job description analysis system.

Analyze the job description below and extract structured
information.

IMPORTANT RULES:

1. Do not invent information.
2. Only extract information explicitly present.
3. If information is missing, return null.
4. Extract technical and professional skills.
5. Separate required skills from preferred skills.
6. Extract education requirements.
7. Extract experience requirements.
8. Extract the main job responsibilities.
9. Preserve the original meaning.
10. Return only the requested structured information.

JOB DESCRIPTION:

{job_description}
"""


def analyze_job_with_ai(
    job_description: str,
) -> StructuredJob:
    """
    Extract structured data from a job description.

    Raises GeminiServiceError (see services/gemini_client.py) if the AI
    service fails. Model choice, timeout and fallback live in that file.
    """

    prompt = build_prompt(job_description)

    return generate_structured(
        prompt=prompt,
        schema=StructuredJob,
        task_name="job-analysis",
    )
