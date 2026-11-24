"""
Learning-plan API.

    POST   /learning-plans                  create a plan (or return the saved one)
    GET    /learning-plans                  list my plans
    GET    /learning-plans/by-match/{id}    my plan for a match, if any
    GET    /learning-plans/{id}             one plan with skills, weeks, tasks
    PATCH  /learning-plans/tasks/{id}       mark a task completed / not completed
    DELETE /learning-plans/{id}             delete a plan

Every query is filtered by the logged-in user, so nobody can read or change
another user's plan.
"""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import (
    JobAnalysis,
    LearningPlan,
    LearningPlanSkill,
    LearningPlanTask,
    LearningPlanWeek,
    MatchResult,
    Resume,
    ResumeEducation,
    ResumeExperience,
    ResumeSkillAddition,
    ResumeSkill,
    
)
from schemas import LearningPlanRequest, TaskUpdate, ResumeSkillAdditionUpdate
from services.gemini_client import GeminiServiceError
from services.learning_plan import (
    build_roadmap,
    compute_progress,
    order_skills,
    reconcile_guides,
    select_skills_for_plan,
    summarize_experience,
)
from services.learning_plan_ai import LearningContext, generate_learning_guides
from services.matching import normalize_skill
from services.skill_gap import generate_skill_gaps

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning-plans", tags=["Learning Plans"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json_list(value) -> list:
    if not value:
        return []

    try:
        loaded = json.loads(value)
    except (TypeError, ValueError):
        return []

    return loaded if isinstance(loaded, list) else []


def serialize_plan(plan: LearningPlan, created: bool | None = None) -> dict:
    tasks = [task for week in plan.weeks for task in week.tasks]
    completed = sum(1 for task in tasks if task.is_completed)

    data = {
        "plan_id": plan.id,
        "match_id": plan.match_id,
        "job_id": plan.job_id,
        "title": plan.title,
        "overview": plan.overview,
        "hours_per_week": plan.hours_per_week,
        "total_weeks": plan.total_weeks,
        "total_hours": plan.total_hours,
        "created_at": plan.created_at,
        "progress": compute_progress(completed, len(tasks)),
        "skills": [
            {
                "skill": skill.skill,
                "category": skill.category,
                "priority": skill.priority,
                "difficulty": skill.difficulty,
                "why_it_matters": skill.why_it_matters,
                "starting_point": skill.starting_point,
                "estimated_hours": skill.estimated_hours,
                "prerequisites": skill.prerequisites,
                "learning_objectives": skill.learning_objectives,
                "beginner_topics": skill.beginner_topics,
                "intermediate_topics": skill.intermediate_topics,
                "advanced_topics": skill.advanced_topics,
                "practical_exercises": skill.practical_exercises,
                "mini_project": skill.mini_project,
                "resources": skill.resources,
                "expected_outcome": skill.expected_outcome,
            }
            for skill in plan.skills
        ],
        "weeks": [
            {
                "week_id": week.id,
                "week_number": week.week_number,
                "skill": week.skill,
                "title": week.title,
                "expected_outcome": week.expected_outcome,
                "tasks": [
                    {
                        "task_id": task.id,
                        "task_type": task.task_type,
                        "description": task.description,
                        "estimated_hours": task.estimated_hours,
                        "is_completed": task.is_completed,
                        "completed_at": task.completed_at,
                    }
                    for task in week.tasks
                ],
            }
            for week in plan.weeks
        ],
    }

    if created is not None:
        data["created"] = created

    return data


def get_owned_plan(db: Session, plan_id: int, user_id: int) -> LearningPlan:
    plan = (
        db.query(LearningPlan)
        .filter(LearningPlan.id == plan_id, LearningPlan.user_id == user_id)
        .first()
    )

    if plan is None:
        raise HTTPException(status_code=404, detail="Learning plan not found.")

    return plan


def build_learning_context(
    db: Session,
    resume: Resume,
    job: JobAnalysis,
    selected_gaps,
    required_keys: set[str],
    hours_per_week: int,
) -> LearningContext:
    """Collect the user's real data for the AI prompt."""

    skill_rows = (
        db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume.id).all()
    )
    education_rows = (
        db.query(ResumeEducation)
        .filter(ResumeEducation.resume_id == resume.id)
        .all()
    )
    experience_rows = (
        db.query(ResumeExperience)
        .filter(ResumeExperience.resume_id == resume.id)
        .all()
    )

    education = []

    for row in education_rows:
        parts = [part for part in (row.degree, row.university) if part]
        if parts:
            education.append(" - ".join(parts))

    experience = [
        {
            "job_title": row.job_title,
            "company": row.company,
            "start_date": row.start_date,
            "end_date": row.end_date,
        }
        for row in experience_rows
    ]

    return LearningContext(
        job_title=job.job_title,
        company=job.company,
        responsibilities=_load_json_list(job.responsibilities),
        resume_skills=[row.skill_name for row in skill_rows],
        education=education,
        experience_summary=summarize_experience(experience),
        gaps=[
            {
                "skill": gap.skill,
                "category": gap.category,
                "priority": gap.priority,
                "required": normalize_skill(gap.skill) in required_keys,
            }
            for gap in selected_gaps
        ],
        hours_per_week=hours_per_week,
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.post("")
def create_learning_plan(
    request: LearningPlanRequest,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match = (
        db.query(MatchResult)
        .filter(
            MatchResult.id == request.match_id,
            MatchResult.user_id == current_user,
        )
        .first()
    )

    if match is None:
        raise HTTPException(status_code=404, detail="Match result not found.")

    # A saved plan is returned as it is. The AI is only called again when the
    # user explicitly asks to regenerate.
    existing = (
        db.query(LearningPlan)
        .filter(
            LearningPlan.user_id == current_user,
            LearningPlan.match_id == match.id,
        )
        .first()
    )

    if existing is not None and not request.regenerate:
        return serialize_plan(existing, created=False)

    job = (
        db.query(JobAnalysis)
        .filter(
            JobAnalysis.id == match.job_id,
            JobAnalysis.user_id == current_user,
        )
        .first()
    )

    resume = (
        db.query(Resume)
        .filter(Resume.id == match.resume_id, Resume.user_id == current_user)
        .first()
    )

    if job is None or resume is None:
        raise HTTPException(
            status_code=404,
            detail="The resume or job for this match no longer exists.",
        )

    required_skills = _load_json_list(job.required_skills)

    gaps = generate_skill_gaps(
        _load_json_list(match.missing_skills),
        required_skills,
    )

    if not gaps:
        raise HTTPException(
            status_code=400,
            detail="There are no skill gaps for this job, so there is "
                   "nothing to plan.",
        )

    selected = select_skills_for_plan(gaps)

    required_keys = {normalize_skill(skill) for skill in required_skills}

    context = build_learning_context(
        db, resume, job, selected, required_keys, request.hours_per_week
    )

    # The AI is called BEFORE anything is deleted, so a failed regeneration
    # never destroys the plan the user already has.
    try:
        ai_result = generate_learning_guides(context)

    except GeminiServiceError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=f"Learning plan generation failed: {error.message}",
        )

    except Exception:
        logger.exception("Unexpected error during learning plan generation")
        raise HTTPException(
            status_code=500,
            detail="Learning plan generation failed due to an unexpected "
                   "server error.",
        )

    skills = order_skills(reconcile_guides(ai_result.guides, selected))

    if not skills:
        raise HTTPException(
            status_code=502,
            detail="The AI service did not return a usable learning plan. "
                   "Please try again.",
        )

    roadmap = build_roadmap(skills, request.hours_per_week)

    try:
        if existing is not None:
            db.delete(existing)
            db.flush()

        plan = LearningPlan(
            user_id=current_user,
            match_id=match.id,
            job_id=job.id,
            title=f"Learning plan for {job.job_title or 'your target job'}",
            overview=(ai_result.overview or "").strip() or None,
            hours_per_week=request.hours_per_week,
            total_weeks=len(roadmap),
            total_hours=sum(skill.estimated_hours for skill in skills),
        )

        for index, skill in enumerate(skills):
            plan.skills.append(
                LearningPlanSkill(order_index=index, **skill.model_dump())
            )

        db.add(plan)
        db.flush()  # the plan now has an id

        for week in roadmap:
            week_row = LearningPlanWeek(
                week_number=week.week_number,
                skill=week.skill,
                title=week.title,
                expected_outcome=week.expected_outcome,
            )

            for task_index, task in enumerate(week.tasks):
                week_row.tasks.append(
                    LearningPlanTask(
                        plan_id=plan.id,
                        order_index=task_index,
                        skill=task.skill,
                        task_type=task.task_type,
                        description=task.description,
                        estimated_hours=task.estimated_hours,
                    )
                )

            plan.weeks.append(week_row)

        db.commit()

    except IntegrityError:
        # Two requests created the plan at the same moment; keep the winner.
        db.rollback()

        winner = (
            db.query(LearningPlan)
            .filter(
                LearningPlan.user_id == current_user,
                LearningPlan.match_id == match.id,
            )
            .first()
        )

        if winner is None:
            logger.exception("Could not save learning plan")
            raise HTTPException(
                status_code=500, detail="Could not save the learning plan."
            )

        return serialize_plan(winner, created=False)

    db.refresh(plan)

    logger.info(
        "Learning plan %s saved for user %s (%s skills, %s weeks)",
        plan.id, current_user, len(skills), len(roadmap),
    )

    return serialize_plan(plan, created=True)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

@router.get("")
def list_learning_plans(
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plans = (
        db.query(LearningPlan)
        .filter(LearningPlan.user_id == current_user)
        .order_by(LearningPlan.id.desc())
        .all()
    )

    if not plans:
        return {"plans": []}

    plan_ids = [plan.id for plan in plans]

    task_rows = (
        db.query(LearningPlanTask.plan_id, LearningPlanTask.is_completed)
        .filter(LearningPlanTask.plan_id.in_(plan_ids))
        .all()
    )

    totals: dict[int, int] = {}
    done: dict[int, int] = {}

    for plan_id, is_completed in task_rows:
        totals[plan_id] = totals.get(plan_id, 0) + 1
        if is_completed:
            done[plan_id] = done.get(plan_id, 0) + 1

    jobs = {
        job.id: job
        for job in db.query(JobAnalysis)
        .filter(JobAnalysis.id.in_([plan.job_id for plan in plans]))
        .all()
    }

    return {
        "plans": [
            {
                "plan_id": plan.id,
                "match_id": plan.match_id,
                "job_id": plan.job_id,
                "title": plan.title,
                "job_title": jobs[plan.job_id].job_title if plan.job_id in jobs else None,
                "company": jobs[plan.job_id].company if plan.job_id in jobs else None,
                "total_weeks": plan.total_weeks,
                "total_hours": plan.total_hours,
                "created_at": plan.created_at,
                "progress": compute_progress(
                    done.get(plan.id, 0), totals.get(plan.id, 0)
                ),
            }
            for plan in plans
        ]
    }


# This route must be declared before "/{plan_id}".
@router.get("/by-match/{match_id}")
def get_plan_by_match(
    match_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = (
        db.query(LearningPlan)
        .filter(
            LearningPlan.user_id == current_user,
            LearningPlan.match_id == match_id,
        )
        .first()
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="No learning plan exists for this match yet.",
        )

    return serialize_plan(plan)


@router.get("/{plan_id}")
def get_learning_plan(
    plan_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return serialize_plan(get_owned_plan(db, plan_id, current_user))


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

@router.patch("/tasks/{task_id}")
def update_task(
    task_id: int,
    update: TaskUpdate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = (
        db.query(LearningPlanTask)
        .join(LearningPlan, LearningPlan.id == LearningPlanTask.plan_id)
        .filter(
            LearningPlanTask.id == task_id,
            LearningPlan.user_id == current_user,
        )
        .first()
    )

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    task.is_completed = update.completed
    task.completed_at = (
        datetime.now(timezone.utc) if update.completed else None
    )

    db.commit()
    db.refresh(task)

    rows = (
        db.query(LearningPlanTask.is_completed)
        .filter(LearningPlanTask.plan_id == task.plan_id)
        .all()
    )

    return {
        "task_id": task.id,
        "is_completed": task.is_completed,
        "completed_at": task.completed_at,
        "progress": compute_progress(
            sum(1 for (flag,) in rows if flag), len(rows)
        ),
    }


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete("/{plan_id}")
def delete_learning_plan(
    plan_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = get_owned_plan(db, plan_id, current_user)

    db.delete(plan)
    db.commit()

    return {"message": "Learning plan deleted."}

# ---------------------------------------------------------------------------
# Resume skill suggestions
# ---------------------------------------------------------------------------

def _serialize_skill_addition(item: ResumeSkillAddition) -> dict:
    return {
        "id": item.id,
        "skill": item.skill,
        "evidence_level": item.evidence_level,
        "suggestion_text": item.suggestion_text,
        "source_task_ids": item.source_task_ids or [],
        "is_selected": item.is_selected,
        "is_approved": item.is_approved,
    }


def _get_completed_task_evidence(plan: LearningPlan):
    """
    Classify completed tasks using their task_type and description.

    Study/topic tasks -> Learned
    Exercise/practice tasks -> Practiced
    Project/build tasks -> Demonstrated
    """
    grouped = {}

    for week in plan.weeks:
        for task in week.tasks:
            if not task.is_completed:
                continue

            skill = (task.skill or "").strip()
            if not skill:
                continue

            task_type = (task.task_type or "").lower().replace("-", "_")
            description = (task.description or "").strip()

            if any(word in task_type for word in ("project", "build")):
                evidence_level = "Demonstrated"
            elif any(word in task_type for word in ("exercise", "practice")):
                evidence_level = "Practiced"
            else:
                evidence_level = "Learned"

            # Remove task-description prefixes for cleaner resume wording.
            clean_description = description
            for prefix in ("Study:", "Practice:", "Build:"):
                if clean_description.lower().startswith(prefix.lower()):
                    clean_description = clean_description[len(prefix):].strip()
                    break

            key = (skill.casefold(), evidence_level)

            if key not in grouped:
                grouped[key] = {
                    "skill": skill,
                    "evidence_level": evidence_level,
                    "descriptions": [],
                    "task_ids": [],
                }

            if clean_description:
                grouped[key]["descriptions"].append(clean_description)

            grouped[key]["task_ids"].append(task.id)

    return grouped


def _make_resume_suggestion(skill: str, evidence_level: str, descriptions: list[str]) -> str:
    """
    Produce factual resume wording from completed learning-plan tasks.
    No claims of employment, years of experience, certification, or mastery.
    """
    details = "; ".join(dict.fromkeys(descriptions))

    if evidence_level == "Demonstrated":
        if details:
            return (
                f"Completed a practical learning project using {skill}: "
                f"{details}."
            )
        return f"Completed a practical learning project using {skill}."

    if evidence_level == "Practiced":
        if details:
            return f"Practiced {skill} through: {details}."
        return f"Completed practical exercises in {skill}."

    if details:
        return f"Completed structured learning in {skill}, covering: {details}."

    return f"Completed structured learning activities in {skill}."


def _get_owned_resume_for_plan(db: Session, plan: LearningPlan, user_id: int):
    match = (
        db.query(MatchResult)
        .filter(
            MatchResult.id == plan.match_id,
            MatchResult.user_id == user_id,
        )
        .first()
    )

    if match is None:
        raise HTTPException(
            status_code=404,
            detail="The match associated with this learning plan was not found.",
        )

    resume = (
        db.query(Resume)
        .filter(
            Resume.id == match.resume_id,
            Resume.user_id == user_id,
        )
        .first()
    )

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="The resume associated with this learning plan was not found.",
        )

    return resume


def _ensure_plan_completed(plan: LearningPlan):
    tasks = [task for week in plan.weeks for task in week.tasks]

    if not tasks:
        raise HTTPException(
            status_code=400,
            detail="This learning plan has no tasks.",
        )

    completed = sum(1 for task in tasks if task.is_completed)

    if completed != len(tasks):
        raise HTTPException(
            status_code=400,
            detail="Complete all learning-plan tasks before adding skills to your resume.",
        )


@router.post("/{plan_id}/resume-suggestions")
def generate_resume_suggestions(
    plan_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = get_owned_plan(db, plan_id, current_user)

    # Suggestions are available only after all tasks are completed.
    _ensure_plan_completed(plan)

    resume = _get_owned_resume_for_plan(db, plan, current_user)
    grouped = _get_completed_task_evidence(plan)

    if not grouped:
        raise HTTPException(
            status_code=400,
            detail="No completed task evidence was found for resume suggestions.",
        )

    # Create missing suggestions without overwriting user edits.
    for evidence in grouped.values():
        existing = (
            db.query(ResumeSkillAddition)
            .filter(
                ResumeSkillAddition.plan_id == plan.id,
                ResumeSkillAddition.skill == evidence["skill"],
                ResumeSkillAddition.evidence_level == evidence["evidence_level"],
                ResumeSkillAddition.user_id == current_user,
            )
            .first()
        )

        if existing:
            continue

        suggestion = _make_resume_suggestion(
            evidence["skill"],
            evidence["evidence_level"],
            evidence["descriptions"],
        )

        db.add(
            ResumeSkillAddition(
                user_id=current_user,
                resume_id=resume.id,
                plan_id=plan.id,
                skill=evidence["skill"],
                evidence_level=evidence["evidence_level"],
                suggestion_text=suggestion,
                source_task_ids=evidence["task_ids"],
                is_selected=False,
                is_approved=False,
            )
        )

    db.commit()

    additions = (
        db.query(ResumeSkillAddition)
        .filter(
            ResumeSkillAddition.plan_id == plan.id,
            ResumeSkillAddition.user_id == current_user,
        )
        .order_by(ResumeSkillAddition.id.asc())
        .all()
    )

    return {
        "plan_id": plan.id,
        "progress": 100,
        "suggestions": [
            _serialize_skill_addition(item) for item in additions
        ],
    }


@router.get("/{plan_id}/resume-suggestions")
def get_resume_suggestions(
    plan_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = get_owned_plan(db, plan_id, current_user)

    additions = (
        db.query(ResumeSkillAddition)
        .filter(
            ResumeSkillAddition.plan_id == plan.id,
            ResumeSkillAddition.user_id == current_user,
        )
        .order_by(ResumeSkillAddition.id.asc())
        .all()
    )

    return {
        "plan_id": plan.id,
        "suggestions": [
            _serialize_skill_addition(item) for item in additions
        ],
    }


@router.patch("/resume-suggestions/{suggestion_id}")
def update_resume_suggestion(
    suggestion_id: int,
    update: ResumeSkillAdditionUpdate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(ResumeSkillAddition)
        .filter(
            ResumeSkillAddition.id == suggestion_id,
            ResumeSkillAddition.user_id == current_user,
        )
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Resume suggestion not found.",
        )

    # Do not allow editing a previously approved suggestion.
    if item.is_approved:
        raise HTTPException(
            status_code=400,
            detail="This suggestion has already been approved.",
        )

    item.suggestion_text = update.suggestion_text.strip()
    item.is_selected = update.is_selected

    if not item.suggestion_text:
        raise HTTPException(
            status_code=400,
            detail="Suggestion text cannot be empty.",
        )

    db.commit()
    db.refresh(item)

    return _serialize_skill_addition(item)


@router.post("/{plan_id}/resume-suggestions/approve")
def approve_resume_suggestions(
    plan_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = get_owned_plan(db, plan_id, current_user)

    _ensure_plan_completed(plan)

    # Also verify that the resume still belongs to this user.
    _get_owned_resume_for_plan(db, plan, current_user)

    additions = (
        db.query(ResumeSkillAddition)
        .filter(
            ResumeSkillAddition.plan_id == plan.id,
            ResumeSkillAddition.user_id == current_user,
        )
        .all()
    )

    selected = [item for item in additions if item.is_selected]

    if not selected:
        raise HTTPException(
            status_code=400,
            detail="Select at least one suggestion before approving.",
        )

    # Approval is explicit. Only selected items are approved.
    for item in additions:
        item.is_approved = item.is_selected

    db.commit()

    return {
        "message": "Selected resume additions approved.",
        "approved_additions": [
            _serialize_skill_addition(item)
            for item in additions
            if item.is_approved
        ],
    }
