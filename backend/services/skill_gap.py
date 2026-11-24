"""
Skill-gap analysis: turns the list of missing skills into categorized,
prioritized gaps.

Rules (all deterministic):

  Category  - decided by the skill itself (language, framework, database, ...).
  Priority  - decided by the JOB, not by the category:
                High   = the job REQUIRES the skill and it is a technical skill
                Medium = the job only PREFERS it, or it is a professional
                         (soft) skill that is shown through experience
"""

import re

from pydantic import BaseModel

from services.matching import normalize_skill, unique_skills


class SkillGap(BaseModel):
    skill: str
    category: str
    priority: str
    reason: str


# ---------------------------------------------------------------------------
# Category knowledge  (keys are NORMALIZED skill names - see normalize_skill)
# ---------------------------------------------------------------------------

PROGRAMMING_LANGUAGES = {
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go",
    "golang", "rust", "php", "ruby", "kotlin", "swift", "scala", "r",
    "sql", "bash", "dart",
}

FRAMEWORKS = {
    "react", "nextjs", "nodejs", "vue", "angular", "express", "django",
    "flask", "fastapi", "spring", "spring boot", "laravel", "rails",
    "jquery", "bootstrap", "tailwindcss", "redux", "pandas", "numpy",
    "scikit-learn", "tensorflow", "pytorch", "flutter", "react native",
    ".net", "asp.net", "dotnet", "junit", "pytest", "jest",
}

DATABASES = {
    "postgresql", "mysql", "mongodb", "oracle", "sqlite", "redis",
    "sql server", "mssql", "dynamodb", "firebase", "elasticsearch",
    "cassandra", "mariadb", "nosql",
}

TOOLS_AND_PLATFORMS = {
    "git", "github", "gitlab", "docker", "kubernetes", "aws", "azure",
    "gcp", "linux", "jenkins", "ci/cd", "terraform", "jira", "postman",
    "power bi", "tableau", "excel", "figma", "vs code", "nginx",
    "github actions", "ansible",
}

TECHNICAL_CONCEPTS = {
    "rest api", "api", "apis", "graphql", "microservices",
    "software architecture", "system design", "data structures",
    "algorithms", "data structures and algorithms", "dsa",
    "object oriented programming", "oop", "design patterns", "agile",
    "scrum", "testing", "unit testing", "tdd", "machine learning",
    "deep learning", "data analysis", "software development",
    "web development", "devops", "database design", "authentication",
    "version control",
}

# Soft / professional skills are recognised by phrase, because job posts
# word them in many ways ("strong communication skills", "team player", ...).
PROFESSIONAL_PHRASES = [
    "communication", "teamwork", "team player", "collaboration",
    "leadership", "problem solving", "analytical", "critical thinking",
    "time management", "adaptability", "interpersonal", "presentation",
    "stakeholder", "mentoring", "negotiation", "decision making",
    "attention to detail", "organizational", "creativity", "work ethic",
    "self motivated", "customer service", "multitasking",
]

PROFESSIONAL = "Professional Skill"


def is_professional_skill(normalized: str) -> bool:
    return any(
        re.search(rf"\b{re.escape(phrase)}", normalized)
        for phrase in PROFESSIONAL_PHRASES
    )


def classify_category(skill: str) -> str:
    """Return the category of a skill, using its normalized name."""

    key = normalize_skill(skill)

    if key in PROGRAMMING_LANGUAGES:
        return "Programming Language"

    if key in FRAMEWORKS:
        return "Framework / Library"

    if key in DATABASES:
        return "Database"

    if key in TOOLS_AND_PLATFORMS:
        return "Tool / Platform"

    if key in TECHNICAL_CONCEPTS:
        return "Technical Concept"

    if is_professional_skill(key):
        return PROFESSIONAL

    return "Technical Skill"


def decide_priority(category: str, is_required: bool) -> str:
    """
    High   - required by the job and technical.
    Medium - only preferred, or a professional skill (which is shown through
             experience rather than learned from a course).
    """
    if is_required and category != PROFESSIONAL:
        return "High"

    return "Medium"


def build_reason(category: str, is_required: bool) -> str:
    if is_required and category == PROFESSIONAL:
        return (
            "The job requires this skill. It is usually shown through "
            "experience and examples, so make sure your resume demonstrates it."
        )

    if is_required:
        return (
            "The job lists this as a required skill and it was not found "
            "on your resume."
        )

    return (
        "The job lists this as a preferred skill. It is not required, "
        "but it would strengthen your application."
    )


def generate_skill_gaps(
    missing_skills: list[str],
    required_skills: list[str] | None = None,
) -> list[SkillGap]:
    """
    Build the skill gaps for one job.

    missing_skills  - skills from the job that the resume does not show
    required_skills - the job's required skills; any missing skill found here
                      (compared by normalized name) counts as required, the
                      rest are treated as preferred
    """

    required_keys = {
        normalize_skill(skill)
        for skill in (required_skills or [])
        if skill and skill.strip()
    }

    gaps = []

    # unique_skills also protects against duplicates in older saved results.
    for key, skill in unique_skills(missing_skills).items():

        category = classify_category(skill)
        is_required = key in required_keys

        gaps.append(
            SkillGap(
                skill=skill,
                category=category,
                priority=decide_priority(category, is_required),
                reason=build_reason(category, is_required),
            )
        )

    return gaps
