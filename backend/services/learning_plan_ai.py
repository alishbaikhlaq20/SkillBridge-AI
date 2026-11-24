"""
Gemini part of the learning-plan feature.

Gemini writes the learning CONTENT for each skill. It does not decide the
priority, the order, the schedule or the progress - that is done by
services/learning_plan.py.
"""

from pydantic import BaseModel, Field

from services.gemini_client import generate_structured


# Long outputs need more time than the short extraction tasks.
PRIMARY_TIMEOUT_MS = 45_000
FALLBACK_TIMEOUT_MS = 60_000

MAX_SKILLS_IN_PROMPT = 40
MAX_RESPONSIBILITIES_IN_PROMPT = 8


# ---------------------------------------------------------------------------
# Structured output expected from Gemini
# (same pattern as StructuredJob: None defaults and default_factory lists)
# ---------------------------------------------------------------------------

class LearningResource(BaseModel):
    title: str | None = None
    type: str | None = None


class SkillGuide(BaseModel):
    skill: str | None = None
    why_it_matters: str | None = None
    difficulty: str | None = None
    starting_point: str | None = None
    estimated_hours: int | None = None

    prerequisites: list[str] = Field(default_factory=list)
    learning_objectives: list[str] = Field(default_factory=list)
    beginner_topics: list[str] = Field(default_factory=list)
    intermediate_topics: list[str] = Field(default_factory=list)
    advanced_topics: list[str] = Field(default_factory=list)
    practical_exercises: list[str] = Field(default_factory=list)

    mini_project: str | None = None
    resources: list[LearningResource] = Field(default_factory=list)
    expected_outcome: str | None = None


class LearningGuidesAI(BaseModel):
    overview: str | None = None
    guides: list[SkillGuide] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Input: the user's real platform data
# ---------------------------------------------------------------------------

class LearningContext(BaseModel):
    job_title: str | None = None
    company: str | None = None
    responsibilities: list[str] = Field(default_factory=list)

    resume_skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience_summary: str = ""

    # [{"skill": ..., "category": ..., "priority": ..., "required": bool}]
    gaps: list[dict] = Field(default_factory=list)

    hours_per_week: int = 8


def build_prompt(context: LearningContext) -> str:
    skills = ", ".join(context.resume_skills[:MAX_SKILLS_IN_PROMPT]) or "none listed"
    education = "; ".join(context.education[:4]) or "none listed"

    responsibilities = "\n".join(
        f"- {item}"
        for item in context.responsibilities[:MAX_RESPONSIBILITIES_IN_PROMPT]
    ) or "- not specified"

    gap_lines = "\n".join(
        f"- {gap['skill']} ({gap['category']}, "
        f"{'required' if gap.get('required') else 'preferred'} by the job)"
        for gap in context.gaps
    )

    return f"""
You are an experienced career coach and technical mentor.

Write a learning guide for EACH skill gap listed below, for the candidate
described. The candidate wants to become a strong applicant for the target job.

CANDIDATE (facts from their resume - use only these):
- Current skills: {skills}
- Education: {education}
- Experience: {context.experience_summary}
- Available study time: about {context.hours_per_week} hours per week

TARGET JOB:
- Title: {context.job_title or "not specified"}
- Company: {context.company or "not specified"}
- Main responsibilities:
{responsibilities}

SKILL GAPS (write exactly one guide per skill, and copy the skill name exactly):
{gap_lines}

RULES:
1. Use only the candidate facts above. Do not invent experience, projects,
   degrees or certifications.
2. Personalize: if the candidate already knows related skills, say so in
   starting_point and keep beginner_topics short or empty. Do not start from
   absolute beginner level when they already have relevant knowledge.
3. why_it_matters must explain why the skill matters for THIS target job.
4. difficulty must be one of: Beginner, Intermediate, Advanced (how hard it is
   for THIS candidate).
5. estimated_hours is the realistic total number of study hours for this
   candidate to reach working proficiency (between 4 and 60).
6. prerequisites are skills or concepts to know first.
7. Be concise: at most 4 learning_objectives, 5 topics per level, 4 practical
   exercises, 1 mini_project, and 4 resources per skill.
8. A resource is a well-known documentation, course, book or practice site.
   Give only its title and type (Documentation, Course, Book, Tutorial or
   Practice). NEVER include URLs.
9. For professional skills (communication, teamwork, leadership, ...) focus on
   practice and building evidence, not on courses.
10. expected_outcome describes what the candidate can do after finishing.
11. overview is 2-3 sentences summarizing the plan for this candidate.
"""


def generate_learning_guides(context: LearningContext) -> LearningGuidesAI:
    """Ask Gemini for the learning content. Raises GeminiServiceError."""

    return generate_structured(
        prompt=build_prompt(context),
        schema=LearningGuidesAI,
        task_name="learning-plan",
        primary_timeout_ms=PRIMARY_TIMEOUT_MS,
        fallback_timeout_ms=FALLBACK_TIMEOUT_MS,
    )
