"""
Deterministic resume-to-job matching engine.

Every score is calculated with explicit, explainable rules. No AI is used here,
so the same inputs always produce the same score.

Overall score = Skills 50% + Experience 30% + Education 20%
"""

import re
from datetime import date

from pydantic import BaseModel


class MatchResultData(BaseModel):
    overall_score: int
    skills_score: int
    experience_score: int
    education_score: int
    matching_skills: list[str]
    missing_skills: list[str]


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def round_half_up(value: float) -> int:
    """
    Round 0.5 upwards (86.5 -> 87).

    Python's built-in round() uses "banker's rounding" (86.5 -> 86), which is
    surprising in a score shown to users.
    """
    return int(value + 0.5)


def clamp_percent(value: float) -> int:
    """Round a value and keep it inside 0-100."""
    return max(0, min(100, round_half_up(value)))


# ---------------------------------------------------------------------------
# Skill normalization
# ---------------------------------------------------------------------------

# Different spellings of the same skill map to one canonical name.
# To support a new synonym, add one line here.
SKILL_ALIASES = {
    # JavaScript ecosystem
    "js": "javascript",
    "ts": "typescript",
    "react.js": "react",
    "reactjs": "react",
    "react js": "react",
    "next.js": "nextjs",
    "next js": "nextjs",
    "node": "nodejs",
    "node.js": "nodejs",
    "node js": "nodejs",
    "vue.js": "vue",
    "vuejs": "vue",
    "vue js": "vue",
    "express.js": "express",
    "expressjs": "express",
    "express js": "express",
    # Databases
    "postgres": "postgresql",
    "postgres db": "postgresql",
    "postgre sql": "postgresql",
    "mongo": "mongodb",
    "mongo db": "mongodb",
    # Cloud / DevOps
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "microsoft azure": "azure",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    # APIs
    "rest": "rest api",
    "rest apis": "rest api",
    "restful": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",
    "restful web services": "rest api",
    # Web
    "html5": "html",
    "css3": "css",
    "tailwind": "tailwindcss",
    "tailwind css": "tailwindcss",
    # Languages
    "c sharp": "c#",
    "csharp": "c#",
    # General
    "front end": "frontend",
    "back end": "backend",
}


def normalize_text(text: str) -> str:
    """Lowercase, trim and collapse repeated spaces."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_skill(skill: str) -> str:
    """
    Convert a skill name to its canonical form so that formatting and common
    synonym differences do not affect matching.

        "React.js" -> "react"      "Postgres"  -> "postgresql"
        "NextJS"   -> "nextjs"     "REST APIs" -> "rest api"
        "Communication Skills" -> "communication"
    """
    skill = normalize_text(skill)

    # "problem-solving" -> "problem solving"
    skill = re.sub(r"[-_]+", " ", skill)

    # Trailing punctuation only (so ".net" keeps its leading dot).
    skill = skill.rstrip(" .,;:")

    # "communication skills" -> "communication"
    without_suffix = re.sub(r"\s+skills?$", "", skill)
    if without_suffix:
        skill = without_suffix

    return SKILL_ALIASES.get(skill, skill)


def unique_skills(skills: list[str]) -> dict[str, str]:
    """
    Remove duplicates, comparing skills by their normalized form.

    Returns {normalized_name: original_name_as_written}, keeping the first
    spelling and the original order. For example ["React", "React.js", "react"]
    becomes {"react": "React"}.
    """
    unique: dict[str, str] = {}

    for skill in skills:
        if not skill or not skill.strip():
            continue

        key = normalize_skill(skill)

        if key and key not in unique:
            unique[key] = skill.strip()

    return unique


# ---------------------------------------------------------------------------
# Skills score
# ---------------------------------------------------------------------------

def calculate_skills_score(
    resume_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
) -> tuple[int, list[str], list[str]]:
    """
    Calculate the skills score (0-100).

    Required skills are 80% of the skills score, preferred skills 20%.
    Duplicate and synonym spellings are counted once. A skill listed as both
    required and preferred counts only as required.
    """

    resume_keys = set(unique_skills(resume_skills))

    required = unique_skills(required_skills)

    preferred = {
        key: name
        for key, name in unique_skills(preferred_skills).items()
        if key not in required
    }

    matching_required = [
        name for key, name in required.items() if key in resume_keys
    ]
    missing_required = [
        name for key, name in required.items() if key not in resume_keys
    ]
    matching_preferred = [
        name for key, name in preferred.items() if key in resume_keys
    ]
    missing_preferred = [
        name for key, name in preferred.items() if key not in resume_keys
    ]

    required_score = (
        len(matching_required) / len(required) * 100 if required else 100
    )
    preferred_score = (
        len(matching_preferred) / len(preferred) * 100 if preferred else 100
    )

    if required and preferred:
        score = required_score * 0.80 + preferred_score * 0.20
    elif required:
        score = required_score
    elif preferred:
        score = preferred_score
    else:
        score = 0

    return (
        clamp_percent(score),
        matching_required + matching_preferred,
        missing_required + missing_preferred,
    )


# ---------------------------------------------------------------------------
# Experience score
# ---------------------------------------------------------------------------

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

PRESENT_WORDS = ("present", "current", "now", "ongoing", "today")

YEARS_PATTERN = re.compile(
    # "2 years", "2+ years", "3-5 years", "2 to 4 yrs"  -> captures the first number
    r"(\d+)\s*(?:\+|-|\u2013|to)?\s*(?:\d+)?\s*\+?\s*(?:years?|yrs?)"
)


def extract_required_years(requirements: list[str]) -> int | None:
    """
    Find the number of years of experience the job asks for.

    "2+ years" -> 2, "3-5 years" -> 3 (the minimum), "five years" -> 5.
    If several requirements mention years, the largest minimum is used.
    Returns None when no number of years is mentioned.
    """

    text = " ".join(requirements).lower()

    for word, number in NUMBER_WORDS.items():
        text = re.sub(
            rf"\b{word}\b(?=\s*\+?\s*(?:years?|yrs?))",
            str(number),
            text,
        )

    minimums = [int(m) for m in YEARS_PATTERN.findall(text)]
    minimums = [m for m in minimums if m > 0]

    return max(minimums) if minimums else None


def parse_year_month(
    value,
    default_month: int,
    today: date,
) -> tuple[int, int] | None:
    """
    Read a free-form date such as "Jan 2021", "03/2020", "2019" or "Present".

    Returns (year, month), or None if the text has no readable year.
    """

    if not value:
        return None

    text = str(value).lower()

    if any(word in text for word in PRESENT_WORDS):
        return today.year, today.month

    year_match = re.search(r"\b((?:19|20)\d{2})\b", text)

    if not year_match:
        return None

    year = int(year_match.group(1))
    month = default_month

    for name, number in MONTHS.items():
        if re.search(rf"\b{name}", text):
            month = number
            break
    else:
        numeric = re.search(
            r"\b(\d{1,2})\s*[/\-.]\s*(?:19|20)\d{2}\b", text
        )
        if numeric and 1 <= int(numeric.group(1)) <= 12:
            month = int(numeric.group(1))

    return year, month


def estimate_years_of_experience(
    resume_experience: list,
    today: date | None = None,
) -> float | None:
    """
    Estimate total years of work experience from start/end dates.

    Overlapping jobs are merged so the same period is not counted twice.
    Returns None if no entry has readable dates.
    """

    today = today or date.today()

    intervals = []

    for item in resume_experience:
        if not isinstance(item, dict):
            continue

        # A year with no month is treated as mid-year so that
        # "2019 - 2021" counts as 2 years rather than 1 or 3.
        start = parse_year_month(item.get("start_date"), 7, today)
        end = parse_year_month(item.get("end_date"), 7, today)

        if not start or not end:
            continue

        start_index = start[0] * 12 + start[1]
        end_index = end[0] * 12 + end[1]

        if end_index > start_index:
            intervals.append((start_index, end_index))

    if not intervals:
        return None

    intervals.sort()

    merged = [list(intervals[0])]

    for start_index, end_index in intervals[1:]:
        if start_index <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end_index)
        else:
            merged.append([start_index, end_index])

    total_months = sum(end - start for start, end in merged)

    return total_months / 12


def calculate_experience_score(
    resume_experience: list,
    experience_requirements: list[str],
    today: date | None = None,
) -> int:
    """
    Calculate the experience score (0-100).

    - Job states no experience requirement          -> 100
    - Resume has no experience entries              -> 0
    - Job gives no number of years                  -> 100 (having experience is enough)
    - Job gives years and the resume has dates     -> candidate_years / required_years
    - Job gives years but dates are unreadable      -> 50 (duration cannot be verified)
    """

    if not experience_requirements:
        return 100

    if not resume_experience:
        return 0

    required_years = extract_required_years(experience_requirements)

    if required_years is None:
        return 100

    candidate_years = estimate_years_of_experience(
        resume_experience, today
    )

    if candidate_years is None:
        return 50

    return clamp_percent(candidate_years / required_years * 100)


# ---------------------------------------------------------------------------
# Education score
# ---------------------------------------------------------------------------

def calculate_education_score(
    resume_education: list,
    education_requirements: list[str],
) -> int:
    """
    Calculate education compatibility.

    If the job has no education requirement, return a full score.
    """

    if not education_requirements:
        return 100

    if not resume_education:
        return 0

    resume_text = " ".join(
        str(item)
        for item in resume_education
    ).lower()

    requirement_text = " ".join(
        education_requirements
    ).lower()

    keywords = [
        "computer science",
        "software engineering",
        "information technology",
        "information systems",
        "engineering",
    ]

    relevant_requirement = any(
        keyword in requirement_text
        for keyword in keywords
    )

    relevant_resume = any(
        keyword in resume_text
        for keyword in keywords
    )

    if relevant_requirement and relevant_resume:
        return 100

    if relevant_resume:
        return 80

    return 50


# ---------------------------------------------------------------------------
# Overall match
# ---------------------------------------------------------------------------

def calculate_match(
    resume_skills: list[str],
    resume_experience: list,
    resume_education: list,
    required_skills: list[str],
    preferred_skills: list[str],
    experience_requirements: list[str],
    education_requirements: list[str],
) -> MatchResultData:

    skills_score, matching_skills, missing_skills = (
        calculate_skills_score(
            resume_skills,
            required_skills,
            preferred_skills,
        )
    )

    experience_score = calculate_experience_score(
        resume_experience,
        experience_requirements,
    )

    education_score = calculate_education_score(
        resume_education,
        education_requirements,
    )

    overall_score = clamp_percent(
        (skills_score * 0.50)
        + (experience_score * 0.30)
        + (education_score * 0.20)
    )

    return MatchResultData(
        overall_score=overall_score,
        skills_score=skills_score,
        experience_score=experience_score,
        education_score=education_score,
        matching_skills=matching_skills,
        missing_skills=missing_skills,
    )
