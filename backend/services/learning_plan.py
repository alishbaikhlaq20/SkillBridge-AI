"""
Deterministic learning-plan logic.

Gemini only WRITES the learning content for each skill (topics, exercises,
resources, ...). Everything that must be reliable and explainable is decided
here, in plain code:

  * which skills go into the plan and in what order
  * priority and category of each skill (they come from the skill-gap analysis)
  * how many weeks each skill takes and what happens in each week
  * progress (completed tasks / total tasks)

Because none of this uses AI, the same input always gives the same roadmap.
"""

import math
from datetime import date

from pydantic import BaseModel

from services.matching import (
    estimate_years_of_experience,
    normalize_skill,
    round_half_up,
)
from services.skill_gap import SkillGap


# ---------------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------------

MAX_PLAN_SKILLS = 6        # a plan covers the top gaps, not all of them
MIN_SKILL_HOURS = 4
MAX_SKILL_HOURS = 60
MAX_WEEKS_PER_SKILL = 8

MAX_ITEMS = {
    "prerequisites": 5,
    "learning_objectives": 5,
    "beginner_topics": 6,
    "intermediate_topics": 6,
    "advanced_topics": 6,
    "practical_exercises": 5,
    "resources": 5,
}
MAX_TEXT_LENGTH = 500

VALID_DIFFICULTIES = ("Beginner", "Intermediate", "Advanced")


# ---------------------------------------------------------------------------
# Data shapes used between the AI layer, this module and the database
# ---------------------------------------------------------------------------

class PlannedSkill(BaseModel):
    """One skill of the plan: AI-written content + deterministic fields."""

    skill: str
    category: str
    priority: str
    difficulty: str
    why_it_matters: str
    starting_point: str
    estimated_hours: int
    prerequisites: list[str]
    learning_objectives: list[str]
    beginner_topics: list[str]
    intermediate_topics: list[str]
    advanced_topics: list[str]
    practical_exercises: list[str]
    mini_project: str
    resources: list[dict]
    expected_outcome: str


class PlannedTask(BaseModel):
    skill: str
    task_type: str            # study | exercise | project
    description: str
    estimated_hours: float


class PlannedWeek(BaseModel):
    week_number: int
    skill: str
    title: str
    expected_outcome: str
    tasks: list[PlannedTask]


# ---------------------------------------------------------------------------
# Choosing the skills for the plan
# ---------------------------------------------------------------------------

def select_skills_for_plan(
    gaps: list[SkillGap],
    limit: int = MAX_PLAN_SKILLS,
) -> list[SkillGap]:
    """High-priority gaps first, then the rest, keeping the original order."""

    high = [gap for gap in gaps if gap.priority == "High"]
    others = [gap for gap in gaps if gap.priority != "High"]

    return (high + others)[:limit]


# ---------------------------------------------------------------------------
# Cleaning the AI output
# ---------------------------------------------------------------------------

def clean_text(value, limit: int = MAX_TEXT_LENGTH) -> str:
    if value is None:
        return ""

    text = " ".join(str(value).split())

    return text[:limit]


def clean_list(values, max_items: int) -> list[str]:
    """Trim, drop empty entries and duplicates, and cap the length."""

    cleaned: list[str] = []
    seen: set[str] = set()

    for value in values or []:
        text = clean_text(value)

        if not text or text.lower() in seen:
            continue

        seen.add(text.lower())
        cleaned.append(text)

        if len(cleaned) >= max_items:
            break

    return cleaned


def clean_resources(resources, max_items: int) -> list[dict]:
    """
    Keep resources as {title, type}. The AI is told not to give URLs, and any
    that slip through are not stored (a made-up link is worse than no link).
    """

    cleaned: list[dict] = []
    seen: set[str] = set()

    for resource in resources or []:
        title = clean_text(getattr(resource, "title", ""), 150)
        kind = clean_text(getattr(resource, "type", ""), 40) or "Resource"

        if not title or "http://" in title or "https://" in title:
            continue

        if title.lower() in seen:
            continue

        seen.add(title.lower())
        cleaned.append({"title": title, "type": kind})

        if len(cleaned) >= max_items:
            break

    return cleaned


def normalize_difficulty(value) -> str:
    text = clean_text(value, 40).lower()

    for difficulty in VALID_DIFFICULTIES:
        if difficulty.lower() == text:
            return difficulty

    return "Intermediate"


def clamp_hours(value) -> int:
    try:
        hours = int(value)
    except (TypeError, ValueError):
        hours = 0

    if hours <= 0:
        hours = 20   # neutral default when the AI gave no usable estimate

    return max(MIN_SKILL_HOURS, min(MAX_SKILL_HOURS, hours))


def reconcile_guides(guides, selected_gaps: list[SkillGap]) -> list[PlannedSkill]:
    """
    Match the AI's guides to the skills we asked about.

    * Guides are matched by normalized skill name, so "Next.js" and "NextJS"
      are the same skill.
    * The skill name, category and priority always come from the skill-gap
      analysis, never from the AI.
    * Guides for skills we did not ask about are ignored.
    * A skill the AI forgot is simply left out of the plan.
    """

    by_key = {}

    for guide in guides or []:
        key = normalize_skill(getattr(guide, "skill", "") or "")

        if key and key not in by_key:
            by_key[key] = guide

    planned: list[PlannedSkill] = []

    for gap in selected_gaps:
        guide = by_key.get(normalize_skill(gap.skill))

        if guide is None:
            continue

        planned.append(
            PlannedSkill(
                skill=gap.skill,
                category=gap.category,
                priority=gap.priority,
                difficulty=normalize_difficulty(guide.difficulty),
                why_it_matters=clean_text(guide.why_it_matters),
                starting_point=clean_text(guide.starting_point),
                estimated_hours=clamp_hours(guide.estimated_hours),
                prerequisites=clean_list(
                    guide.prerequisites, MAX_ITEMS["prerequisites"]
                ),
                learning_objectives=clean_list(
                    guide.learning_objectives, MAX_ITEMS["learning_objectives"]
                ),
                beginner_topics=clean_list(
                    guide.beginner_topics, MAX_ITEMS["beginner_topics"]
                ),
                intermediate_topics=clean_list(
                    guide.intermediate_topics, MAX_ITEMS["intermediate_topics"]
                ),
                advanced_topics=clean_list(
                    guide.advanced_topics, MAX_ITEMS["advanced_topics"]
                ),
                practical_exercises=clean_list(
                    guide.practical_exercises, MAX_ITEMS["practical_exercises"]
                ),
                mini_project=clean_text(guide.mini_project),
                resources=clean_resources(
                    guide.resources, MAX_ITEMS["resources"]
                ),
                expected_outcome=clean_text(guide.expected_outcome),
            )
        )

    return planned


# ---------------------------------------------------------------------------
# Ordering: learn prerequisites first
# ---------------------------------------------------------------------------

def order_skills(skills: list[PlannedSkill]) -> list[PlannedSkill]:
    """
    Keep the priority order, but place a skill after any other skill in the
    plan that it lists as a prerequisite. Cycles cannot cause a loop: when no
    skill is ready, the first remaining one is taken.
    """

    remaining = list(skills)
    ordered: list[PlannedSkill] = []
    placed: set[str] = set()
    plan_keys = {normalize_skill(skill.skill) for skill in skills}

    while remaining:
        chosen = None

        for skill in remaining:
            own_key = normalize_skill(skill.skill)

            needed = {
                normalize_skill(prerequisite)
                for prerequisite in skill.prerequisites
            }
            needed = {
                key for key in needed
                if key in plan_keys and key != own_key
            }

            if needed <= placed:
                chosen = skill
                break

        if chosen is None:
            chosen = remaining[0]

        remaining.remove(chosen)
        ordered.append(chosen)
        placed.add(normalize_skill(chosen.skill))

    return ordered


# ---------------------------------------------------------------------------
# Weekly roadmap
# ---------------------------------------------------------------------------

def _split_evenly(items: list, parts: int) -> list[list]:
    """Split a list into `parts` consecutive groups of near-equal size."""

    base, extra = divmod(len(items), parts)
    groups = []
    start = 0

    for index in range(parts):
        size = base + (1 if index < extra else 0)
        groups.append(items[start:start + size])
        start += size

    return groups


def _tasks_for_skill(skill: PlannedSkill) -> list[PlannedTask]:
    """
    Turn a skill's content into an ordered list of tasks:
    study topics (beginner -> advanced), then exercises, then the mini-project.
    """

    descriptions: list[tuple[str, str]] = []

    for topic in (
        skill.beginner_topics
        + skill.intermediate_topics
        + skill.advanced_topics
    ):
        descriptions.append(("study", f"Study: {topic}"))

    for exercise in skill.practical_exercises:
        descriptions.append(("exercise", f"Practice: {exercise}"))

    if skill.mini_project:
        descriptions.append(("project", f"Build: {skill.mini_project}"))

    if not descriptions:
        descriptions.append(
            ("study", f"Study the fundamentals of {skill.skill}")
        )

    hours_each = max(
        0.5, round(skill.estimated_hours / len(descriptions), 1)
    )

    return [
        PlannedTask(
            skill=skill.skill,
            task_type=task_type,
            description=description,
            estimated_hours=hours_each,
        )
        for task_type, description in descriptions
    ]


def build_roadmap(
    skills: list[PlannedSkill],
    hours_per_week: int,
) -> list[PlannedWeek]:
    """
    Build the week-by-week roadmap.

    One skill is the focus at a time. A skill needs
    ceil(estimated_hours / hours_per_week) weeks (at most 8, never more weeks
    than it has tasks). Its tasks are spread across those weeks in order, so
    the mini-project always lands in the skill's last week.
    """

    hours_per_week = max(1, hours_per_week)

    weeks: list[PlannedWeek] = []
    week_number = 1

    for skill in skills:
        tasks = _tasks_for_skill(skill)

        weeks_needed = math.ceil(skill.estimated_hours / hours_per_week)
        weeks_needed = max(1, min(MAX_WEEKS_PER_SKILL, weeks_needed))
        weeks_needed = min(weeks_needed, len(tasks))

        groups = _split_evenly(tasks, weeks_needed)

        for index, group in enumerate(groups):
            is_first = index == 0
            is_last = index == weeks_needed - 1

            if weeks_needed == 1:
                stage = "Learn and apply"
            elif is_first:
                stage = "Getting started"
            elif is_last:
                stage = "Apply and build"
            else:
                stage = "Going deeper"

            if is_last:
                outcome = skill.expected_outcome or (
                    f"You can use {skill.skill} confidently in a small project."
                )
            elif index < len(skill.learning_objectives):
                outcome = skill.learning_objectives[index]
            else:
                outcome = f"Progress through the planned {skill.skill} topics."

            weeks.append(
                PlannedWeek(
                    week_number=week_number,
                    skill=skill.skill,
                    title=f"{skill.skill}: {stage}",
                    expected_outcome=outcome,
                    tasks=group,
                )
            )

            week_number += 1

    return weeks


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

def compute_progress(completed: int, total: int) -> dict:
    percent = round_half_up(completed / total * 100) if total else 0

    return {
        "completed_tasks": completed,
        "total_tasks": total,
        "percent": percent,
    }


# ---------------------------------------------------------------------------
# Candidate summary used in the AI prompt
# ---------------------------------------------------------------------------

def summarize_experience(
    experience_rows: list[dict],
    today: date | None = None,
) -> str:
    """Short, factual description of the candidate's experience."""

    if not experience_rows:
        return "No work experience listed on the resume."

    titles = []

    for row in experience_rows:
        title = clean_text(row.get("job_title"), 80)
        company = clean_text(row.get("company"), 80)

        if title and company:
            titles.append(f"{title} at {company}")
        elif title:
            titles.append(title)

    years = estimate_years_of_experience(experience_rows, today)

    parts = []

    if years is not None:
        parts.append(f"About {years:.1f} years of experience")

    if titles:
        parts.append("Roles: " + "; ".join(titles[:5]))

    return ". ".join(parts) if parts else "Experience is listed but undated."
