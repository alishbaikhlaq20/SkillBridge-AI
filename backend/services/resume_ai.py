from pydantic import BaseModel, Field

from services.gemini_client import generate_structured


# -----------------------------
# Structured output schemas
# -----------------------------

class EducationExtraction(BaseModel):
    degree: str | None = None
    university: str | None = None
    location: str | None = None
    cgpa: float | None = None
    graduation_year: int | None = None


class ExperienceExtraction(BaseModel):
    company: str | None = None
    job_title: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: list[str] = Field(default_factory=list)


class StructuredResume(BaseModel):
    skills: list[str] = Field(default_factory=list)
    education: list[EducationExtraction] = Field(default_factory=list)
    experience: list[ExperienceExtraction] = Field(default_factory=list)


# -----------------------------
# AI resume extraction
# -----------------------------

def build_prompt(resume_text: str) -> str:
    return f"""
You are a professional resume information extraction system.

Analyze the resume text below and extract structured information.

IMPORTANT RULES:

1. Do not invent information.
2. Only extract information explicitly present in the resume.
3. If information is missing, return null.
4. Extract technical and professional skills.
5. Separate different education entries.
6. Separate different work experience entries.
7. Keep experience descriptions as separate bullet points when possible.
8. Normalize obvious formatting differences.
9. Preserve the original meaning of the resume.
10. Return only the requested structured information.

RESUME TEXT:

{resume_text}
"""


def extract_resume_with_ai(
    resume_text: str,
) -> StructuredResume:
    """
    Extract structured data from resume text.

    Raises GeminiServiceError (see services/gemini_client.py) if the AI
    service fails. Model choice, timeout and fallback live in that file.
    """

    prompt = build_prompt(resume_text)

    return generate_structured(
        prompt=prompt,
        schema=StructuredResume,
        task_name="resume-analysis",
    )
