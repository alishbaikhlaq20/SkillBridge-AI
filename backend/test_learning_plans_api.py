"""
API tests for learning plans. Gemini is mocked, so these tests are free,
fast and never need an API key or internet access.

Run from the backend folder:  python -m pytest -v
"""

import pytest

from database import SessionLocal
from models import (
    LearningPlan,
    LearningPlanSkill,
    LearningPlanTask,
    LearningPlanWeek,
)
from routers import learning_plans
from services.gemini_client import GeminiServiceError
from services.learning_plan_ai import (
    LearningGuidesAI,
    LearningResource,
    SkillGuide,
)
from tests.conftest import seed_match


# --------------------------------------------------------------------------
# A fake Gemini
# --------------------------------------------------------------------------

class FakeAI:
    """Replaces generate_learning_guides; records how it was called."""

    def __init__(self):
        self.calls = 0
        self.contexts = []
        self.error = None
        self.empty = False

    def __call__(self, context):
        self.calls += 1
        self.contexts.append(context)

        if self.error is not None:
            raise self.error

        if self.empty:
            return LearningGuidesAI(overview="x", guides=[])

        return LearningGuidesAI(
            overview="A focused plan for the missing skills.",
            guides=[
                SkillGuide(
                    skill=item["skill"],
                    why_it_matters=f"{item['skill']} is used daily in this job.",
                    difficulty="Intermediate",
                    starting_point="You already know Python, so skip the basics.",
                    estimated_hours=16,
                    prerequisites=[],
                    learning_objectives=["Understand the core ideas"],
                    beginner_topics=["Core concepts", "Installation"],
                    intermediate_topics=["Real-world usage"],
                    advanced_topics=["Optimization"],
                    practical_exercises=["Small exercise 1", "Small exercise 2"],
                    mini_project=f"A mini project using {item['skill']}",
                    resources=[LearningResource(title="Official docs", type="Documentation")],
                    expected_outcome=f"You can use {item['skill']} in a project.",
                )
                for item in context.gaps
            ],
        )


@pytest.fixture()
def fake_ai(monkeypatch):
    fake = FakeAI()
    monkeypatch.setattr(learning_plans, "generate_learning_guides", fake)
    return fake


def create_plan(client, headers, match_id, **extra):
    return client.post(
        "/learning-plans",
        json={"match_id": match_id, **extra},
        headers=headers,
    )


def table_counts():
    db = SessionLocal()
    try:
        return {
            "plans": db.query(LearningPlan).count(),
            "skills": db.query(LearningPlanSkill).count(),
            "weeks": db.query(LearningPlanWeek).count(),
            "tasks": db.query(LearningPlanTask).count(),
        }
    finally:
        db.close()


# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------

def test_endpoints_require_a_token(client):
    assert client.post("/learning-plans", json={"match_id": 1}).status_code in (401, 403)
    assert client.get("/learning-plans").status_code in (401, 403)
    assert client.get("/learning-plans/1").status_code in (401, 403)
    assert client.get("/learning-plans/by-match/1").status_code in (401, 403)
    assert client.patch("/learning-plans/tasks/1", json={"completed": True}).status_code in (401, 403)
    assert client.delete("/learning-plans/1").status_code in (401, 403)


# --------------------------------------------------------------------------
# Creating a plan
# --------------------------------------------------------------------------

def test_create_plan_saves_everything_and_returns_it(client, user_a, fake_ai):
    ids = seed_match(user_id=1)

    response = create_plan(client, user_a, ids["match_id"], hours_per_week=8)
    assert response.status_code == 200, response.text
    plan = response.json()

    assert plan["created"] is True
    assert plan["match_id"] == ids["match_id"]
    assert plan["job_id"] == ids["job_id"]
    assert "Backend Developer" in plan["title"]
    assert plan["overview"] == "A focused plan for the missing skills."
    assert plan["hours_per_week"] == 8

    # 4 missing skills: Docker, Kubernetes (required), Communication Skills (required, soft), AWS (preferred)
    skills = {s["skill"]: s for s in plan["skills"]}
    assert set(skills) == {"Docker", "Kubernetes", "Communication Skills", "AWS"}
    assert skills["Docker"]["priority"] == "High"
    assert skills["Communication Skills"]["priority"] == "Medium"
    assert skills["Communication Skills"]["category"] == "Professional Skill"
    assert skills["AWS"]["priority"] == "Medium"

    # high priority skills are scheduled before the medium ones
    week_skills = [w["skill"] for w in plan["weeks"]]
    assert week_skills.index("Docker") < week_skills.index("AWS")

    assert plan["progress"] == {
        "completed_tasks": 0,
        "total_tasks": sum(len(w["tasks"]) for w in plan["weeks"]),
        "percent": 0,
    }
    assert plan["total_weeks"] == len(plan["weeks"])

    counts = table_counts()
    assert counts["plans"] == 1 and counts["skills"] == 4
    assert counts["tasks"] == plan["progress"]["total_tasks"]


def test_ai_receives_the_users_real_data(client, user_a, fake_ai):
    ids = seed_match(user_id=1, resume_skills=("python", "sql"))
    create_plan(client, user_a, ids["match_id"], hours_per_week=12)

    context = fake_ai.contexts[0]
    assert context.job_title == "Backend Developer"
    assert context.company == "Globex"
    assert set(context.resume_skills) == {"python", "sql"}
    assert context.hours_per_week == 12
    assert "Build REST APIs" in context.responsibilities
    assert "Junior Developer at Acme" in context.experience_summary
    assert {g["skill"] for g in context.gaps} == {"Docker", "Kubernetes", "Communication Skills", "AWS"}
    assert {g["skill"]: g["required"] for g in context.gaps}["AWS"] is False
    assert {g["skill"]: g["required"] for g in context.gaps}["Docker"] is True


def test_opening_the_plan_again_does_not_call_the_ai(client, user_a, fake_ai):
    ids = seed_match(user_id=1)

    first = create_plan(client, user_a, ids["match_id"]).json()
    second = create_plan(client, user_a, ids["match_id"]).json()

    assert fake_ai.calls == 1
    assert second["created"] is False
    assert second["plan_id"] == first["plan_id"]
    assert table_counts()["plans"] == 1


def test_regenerate_replaces_the_plan_and_resets_progress(client, user_a, fake_ai):
    ids = seed_match(user_id=1)

    first = create_plan(client, user_a, ids["match_id"]).json()
    task_id = first["weeks"][0]["tasks"][0]["task_id"]
    client.patch(f"/learning-plans/tasks/{task_id}", json={"completed": True}, headers=user_a)

    again = create_plan(client, user_a, ids["match_id"], regenerate=True).json()

    assert fake_ai.calls == 2
    assert again["created"] is True
    assert again["progress"]["completed_tasks"] == 0
    assert table_counts()["plans"] == 1                       # old plan is gone
    assert table_counts()["tasks"] == again["progress"]["total_tasks"]


def test_failed_regeneration_keeps_the_existing_plan_and_progress(client, user_a, fake_ai):
    ids = seed_match(user_id=1)

    first = create_plan(client, user_a, ids["match_id"]).json()
    task_id = first["weeks"][0]["tasks"][0]["task_id"]
    client.patch(f"/learning-plans/tasks/{task_id}", json={"completed": True}, headers=user_a)

    fake_ai.error = GeminiServiceError("The AI service took too long.", status_code=504, retryable=True)
    response = create_plan(client, user_a, ids["match_id"], regenerate=True)

    assert response.status_code == 504
    kept = client.get(f"/learning-plans/{first['plan_id']}", headers=user_a).json()
    assert kept["progress"]["completed_tasks"] == 1


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------

@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_ai_errors_are_returned_with_their_status_and_nothing_is_saved(client, user_a, fake_ai, status):
    ids = seed_match(user_id=1)
    fake_ai.error = GeminiServiceError("Some clear message.", status_code=status)

    response = create_plan(client, user_a, ids["match_id"])

    assert response.status_code == status
    assert "Learning plan generation failed: Some clear message." in response.json()["detail"]
    assert table_counts() == {"plans": 0, "skills": 0, "weeks": 0, "tasks": 0}


def test_unexpected_ai_error_is_hidden_from_the_user(client, user_a, fake_ai):
    ids = seed_match(user_id=1)
    fake_ai.error = RuntimeError("secret internal detail")

    response = create_plan(client, user_a, ids["match_id"])

    assert response.status_code == 500
    assert "secret internal detail" not in response.text


def test_empty_ai_result_returns_502_and_saves_nothing(client, user_a, fake_ai):
    ids = seed_match(user_id=1)
    fake_ai.empty = True

    response = create_plan(client, user_a, ids["match_id"])

    assert response.status_code == 502
    assert table_counts()["plans"] == 0


def test_no_skill_gaps_means_nothing_to_plan(client, user_a, fake_ai):
    ids = seed_match(user_id=1, missing=())

    response = create_plan(client, user_a, ids["match_id"])

    assert response.status_code == 400
    assert fake_ai.calls == 0


def test_unknown_match_returns_404(client, user_a, fake_ai):
    assert create_plan(client, user_a, 9999).status_code == 404
    assert fake_ai.calls == 0


@pytest.mark.parametrize("hours", [0, 1, 41, 100])
def test_hours_per_week_is_validated(client, user_a, fake_ai, hours):
    ids = seed_match(user_id=1)
    response = create_plan(client, user_a, ids["match_id"], hours_per_week=hours)
    assert response.status_code == 422
    assert fake_ai.calls == 0


def test_a_plan_covers_at_most_six_skills(client, user_a, fake_ai):
    many = tuple(f"Skill{i}" for i in range(10))
    ids = seed_match(user_id=1, required=many, preferred=(), missing=many)

    plan = create_plan(client, user_a, ids["match_id"]).json()

    assert len(plan["skills"]) == 6


# --------------------------------------------------------------------------
# Ownership: users can never reach each other's data
# --------------------------------------------------------------------------

def test_user_cannot_create_a_plan_for_someone_elses_match(client, user_a, user_b, fake_ai):
    ids = seed_match(user_id=1)                      # belongs to user A (id 1)

    response = create_plan(client, user_b, ids["match_id"])

    assert response.status_code == 404
    assert fake_ai.calls == 0
    assert table_counts()["plans"] == 0


def test_user_cannot_read_update_or_delete_someone_elses_plan(client, user_a, user_b, fake_ai):
    ids = seed_match(user_id=1)
    plan = create_plan(client, user_a, ids["match_id"]).json()
    task_id = plan["weeks"][0]["tasks"][0]["task_id"]

    assert client.get(f"/learning-plans/{plan['plan_id']}", headers=user_b).status_code == 404
    assert client.get(f"/learning-plans/by-match/{ids['match_id']}", headers=user_b).status_code == 404
    assert client.patch(f"/learning-plans/tasks/{task_id}", json={"completed": True}, headers=user_b).status_code == 404
    assert client.delete(f"/learning-plans/{plan['plan_id']}", headers=user_b).status_code == 404
    assert client.get("/learning-plans", headers=user_b).json() == {"plans": []}

    # and nothing was changed by those attempts
    still = client.get(f"/learning-plans/{plan['plan_id']}", headers=user_a).json()
    assert still["progress"]["completed_tasks"] == 0


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------

def test_get_plan_by_id_and_by_match(client, user_a, fake_ai):
    ids = seed_match(user_id=1)
    created = create_plan(client, user_a, ids["match_id"]).json()

    by_id = client.get(f"/learning-plans/{created['plan_id']}", headers=user_a).json()
    by_match = client.get(f"/learning-plans/by-match/{ids['match_id']}", headers=user_a).json()

    assert by_id["plan_id"] == by_match["plan_id"] == created["plan_id"]
    assert fake_ai.calls == 1


def test_by_match_returns_404_when_there_is_no_plan(client, user_a):
    ids = seed_match(user_id=1)
    assert client.get(f"/learning-plans/by-match/{ids['match_id']}", headers=user_a).status_code == 404


def test_list_shows_my_plans_with_progress(client, user_a, fake_ai):
    ids = seed_match(user_id=1)
    plan = create_plan(client, user_a, ids["match_id"]).json()

    listing = client.get("/learning-plans", headers=user_a).json()["plans"]

    assert len(listing) == 1
    assert listing[0]["plan_id"] == plan["plan_id"]
    assert listing[0]["job_title"] == "Backend Developer"
    assert listing[0]["progress"]["percent"] == 0
    assert listing[0]["progress"]["total_tasks"] == plan["progress"]["total_tasks"]


# --------------------------------------------------------------------------
# Progress
# --------------------------------------------------------------------------

def test_completing_and_undoing_tasks_updates_progress(client, user_a, fake_ai):
    ids = seed_match(user_id=1)
    plan = create_plan(client, user_a, ids["match_id"]).json()
    total = plan["progress"]["total_tasks"]
    task_id = plan["weeks"][0]["tasks"][0]["task_id"]

    done = client.patch(f"/learning-plans/tasks/{task_id}", json={"completed": True}, headers=user_a).json()
    assert done["is_completed"] is True
    assert done["completed_at"] is not None
    assert done["progress"]["completed_tasks"] == 1
    assert done["progress"]["total_tasks"] == total

    saved = client.get(f"/learning-plans/{plan['plan_id']}", headers=user_a).json()
    assert saved["progress"]["completed_tasks"] == 1
    assert saved["weeks"][0]["tasks"][0]["is_completed"] is True

    undone = client.patch(f"/learning-plans/tasks/{task_id}", json={"completed": False}, headers=user_a).json()
    assert undone["is_completed"] is False
    assert undone["completed_at"] is None
    assert undone["progress"]["completed_tasks"] == 0


def test_completing_every_task_gives_100_percent(client, user_a, fake_ai):
    ids = seed_match(user_id=1)
    plan = create_plan(client, user_a, ids["match_id"]).json()

    last = None
    for week in plan["weeks"]:
        for task in week["tasks"]:
            last = client.patch(
                f"/learning-plans/tasks/{task['task_id']}",
                json={"completed": True}, headers=user_a,
            ).json()

    assert last["progress"]["percent"] == 100


def test_unknown_task_returns_404(client, user_a):
    assert client.patch("/learning-plans/tasks/9999", json={"completed": True}, headers=user_a).status_code == 404


# --------------------------------------------------------------------------
# Deleting
# --------------------------------------------------------------------------

def test_deleting_a_plan_removes_all_its_rows(client, user_a, fake_ai):
    ids = seed_match(user_id=1)
    plan = create_plan(client, user_a, ids["match_id"]).json()

    response = client.delete(f"/learning-plans/{plan['plan_id']}", headers=user_a)

    assert response.status_code == 200
    assert table_counts() == {"plans": 0, "skills": 0, "weeks": 0, "tasks": 0}
    assert client.get(f"/learning-plans/{plan['plan_id']}", headers=user_a).status_code == 404

    # a new plan can be created afterwards
    assert create_plan(client, user_a, ids["match_id"]).json()["created"] is True


# --------------------------------------------------------------------------
# Gemini overload ("high demand" 503) through the real retry/fallback code.
# Only the network call is faked, so gemini_client itself is exercised.
# --------------------------------------------------------------------------

def _guides_for(*names):
    return LearningGuidesAI(
        overview="Plan",
        guides=[
            SkillGuide(
                skill=name, estimated_hours=10, difficulty="Beginner",
                beginner_topics=["Basics"], practical_exercises=["Exercise"],
                mini_project=f"Project with {name}", expected_outcome="Done",
            )
            for name in names
        ],
    )


def _fake_network(monkeypatch, outcomes):
    from services import gemini_client as gc

    calls, sleeps, script = [], [], iter(outcomes)

    def fake_call(model, timeout_ms, prompt, schema):
        calls.append(model)
        outcome = next(script)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(gc, "_call_model", fake_call)
    monkeypatch.setattr(gc.time, "sleep", lambda seconds: sleeps.append(seconds))
    return gc, calls, sleeps


def _overload():
    from google.genai import errors

    return errors.ServerError(
        503, {"error": {"code": 503, "message": "high demand", "status": "UNAVAILABLE"}}
    )


ALL_SKILLS = ("Docker", "Communication Skills", "Kubernetes", "AWS")


def test_a_short_gemini_overload_is_survived_and_the_plan_is_created(client, user_a, monkeypatch):
    gc, calls, sleeps = _fake_network(monkeypatch, [_overload(), _guides_for(*ALL_SKILLS)])
    ids = seed_match(user_id=1)

    response = create_plan(client, user_a, ids["match_id"])

    assert response.status_code == 200, response.text
    assert response.json()["created"] is True
    assert calls == [gc.PRIMARY_MODEL, gc.PRIMARY_MODEL]     # same model, second try worked
    assert sleeps == [gc.RETRY_DELAY_SECONDS]
    assert table_counts()["plans"] == 1


def test_gemini_overloaded_on_both_models_gives_a_clear_503_and_saves_nothing(client, user_a, monkeypatch):
    # exactly what happened in the real log: 503 on the primary AND on the fallback
    gc, calls, sleeps = _fake_network(monkeypatch, [_overload()] * 4)
    ids = seed_match(user_id=1)

    response = create_plan(client, user_a, ids["match_id"])

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]
    assert calls == [gc.PRIMARY_MODEL, gc.PRIMARY_MODEL, gc.FALLBACK_MODEL, gc.FALLBACK_MODEL]
    assert table_counts() == {"plans": 0, "skills": 0, "weeks": 0, "tasks": 0}

    # and the user can simply press the button again once Google recovers
    gc, calls, sleeps = _fake_network(monkeypatch, [_guides_for(*ALL_SKILLS)])
    assert create_plan(client, user_a, ids["match_id"]).json()["created"] is True
