"""
Unit tests for the deterministic learning-plan logic (no database, no AI).

Run from the backend folder:  python -m pytest -v
"""

from datetime import date

from services.learning_plan import (
    MAX_PLAN_SKILLS,
    PlannedSkill,
    build_roadmap,
    clamp_hours,
    clean_list,
    clean_resources,
    compute_progress,
    normalize_difficulty,
    order_skills,
    reconcile_guides,
    select_skills_for_plan,
    summarize_experience,
)
from services.learning_plan_ai import LearningResource, SkillGuide
from services.skill_gap import SkillGap


def gap(skill, priority="High", category="Technical Skill"):
    return SkillGap(skill=skill, category=category, priority=priority, reason="r")


def guide(skill, **kwargs):
    return SkillGuide(skill=skill, **kwargs)


def planned(skill, hours=10, topics=(), exercises=(), project="", prereqs=(), objectives=()):
    return PlannedSkill(
        skill=skill, category="Technical Skill", priority="High",
        difficulty="Intermediate", why_it_matters="w", starting_point="s",
        estimated_hours=hours, prerequisites=list(prereqs),
        learning_objectives=list(objectives), beginner_topics=list(topics),
        intermediate_topics=[], advanced_topics=[],
        practical_exercises=list(exercises), mini_project=project,
        resources=[], expected_outcome="can do it",
    )


# --------------------------------------------------------------------------
# Choosing skills
# --------------------------------------------------------------------------

def test_high_priority_skills_come_first_and_order_is_kept():
    gaps = [gap("A", "Medium"), gap("B", "High"), gap("C", "Medium"), gap("D", "High")]
    assert [g.skill for g in select_skills_for_plan(gaps)] == ["B", "D", "A", "C"]


def test_plan_is_limited_to_the_top_skills():
    gaps = [gap(f"S{i}") for i in range(20)]
    assert len(select_skills_for_plan(gaps)) == MAX_PLAN_SKILLS


# --------------------------------------------------------------------------
# Cleaning AI output
# --------------------------------------------------------------------------

def test_clean_list_drops_empty_and_duplicates_and_caps_length():
    assert clean_list(["a", " a ", "", None, "b", "A", "c"], 2) == ["a", "b"]
    assert clean_list(None, 3) == []


def test_difficulty_is_normalized():
    assert normalize_difficulty("beginner") == "Beginner"
    assert normalize_difficulty(" ADVANCED ") == "Advanced"
    assert normalize_difficulty("very hard") == "Intermediate"
    assert normalize_difficulty(None) == "Intermediate"


def test_hours_are_clamped_and_defaulted():
    assert clamp_hours(1) == 4
    assert clamp_hours(500) == 60
    assert clamp_hours(25) == 25
    assert clamp_hours(None) == 20
    assert clamp_hours(0) == 20
    assert clamp_hours("abc") == 20


def test_resources_keep_title_and_type_and_drop_urls():
    cleaned = clean_resources(
        [
            LearningResource(title="Official FastAPI docs", type="Documentation"),
            LearningResource(title="https://evil.example/x", type="Course"),
            LearningResource(title="official fastapi docs", type="Course"),
            LearningResource(title="", type="Book"),
            LearningResource(title="Clean Code", type=None),
        ],
        5,
    )
    assert cleaned == [
        {"title": "Official FastAPI docs", "type": "Documentation"},
        {"title": "Clean Code", "type": "Resource"},
    ]


# --------------------------------------------------------------------------
# Reconciling AI guides with the requested skills
# --------------------------------------------------------------------------

def test_guides_are_matched_by_normalized_name_and_keep_our_fields():
    result = reconcile_guides(
        [guide("NextJS", difficulty="advanced", estimated_hours=30)],
        [gap("Next.js", "High", "Framework / Library")],
    )
    assert len(result) == 1
    assert result[0].skill == "Next.js"                 # our spelling
    assert result[0].category == "Framework / Library"  # from skill gaps, not AI
    assert result[0].priority == "High"                 # from skill gaps, not AI
    assert result[0].difficulty == "Advanced"


def test_unrequested_guides_are_ignored_and_forgotten_skills_left_out():
    result = reconcile_guides(
        [guide("Docker"), guide("Totally Different Skill")],
        [gap("Docker"), gap("Kubernetes")],
    )
    assert [skill.skill for skill in result] == ["Docker"]


def test_reconcile_handles_missing_fields():
    result = reconcile_guides([guide("Docker")], [gap("Docker")])
    skill = result[0]
    assert skill.estimated_hours == 20 and skill.difficulty == "Intermediate"
    assert skill.beginner_topics == [] and skill.mini_project == ""


def test_reconcile_with_nothing_returns_empty():
    assert reconcile_guides([], [gap("Docker")]) == []
    assert reconcile_guides(None, [gap("Docker")]) == []


# --------------------------------------------------------------------------
# Ordering by prerequisites
# --------------------------------------------------------------------------

def test_prerequisite_skill_is_placed_first():
    ordered = order_skills([
        planned("FastAPI", prereqs=["Python"]),
        planned("Python"),
    ])
    assert [s.skill for s in ordered] == ["Python", "FastAPI"]


def test_prerequisites_outside_the_plan_do_not_change_order():
    ordered = order_skills([
        planned("Docker", prereqs=["Linux basics"]),
        planned("AWS"),
    ])
    assert [s.skill for s in ordered] == ["Docker", "AWS"]


def test_circular_prerequisites_do_not_loop_forever():
    ordered = order_skills([
        planned("A", prereqs=["B"]),
        planned("B", prereqs=["A"]),
    ])
    assert sorted(s.skill for s in ordered) == ["A", "B"]


# --------------------------------------------------------------------------
# Weekly roadmap
# --------------------------------------------------------------------------

def test_weeks_are_numbered_from_one_without_gaps():
    skills = [
        planned("A", hours=16, topics=["t1", "t2", "t3", "t4"], exercises=["e1", "e2"], project="p"),
        planned("B", hours=8, topics=["t1"], exercises=["e1"], project="p"),
    ]
    weeks = build_roadmap(skills, hours_per_week=8)
    assert [w.week_number for w in weeks] == list(range(1, len(weeks) + 1))


def test_number_of_weeks_follows_hours_and_weekly_budget():
    skill = planned("A", hours=20, topics=["a", "b", "c"], exercises=["d", "e"], project="p")
    assert len(build_roadmap([skill], hours_per_week=10)) == 2
    assert len(build_roadmap([skill], hours_per_week=5)) == 4
    assert len(build_roadmap([skill], hours_per_week=40)) == 1


def test_a_skill_never_takes_more_than_eight_weeks_or_more_weeks_than_tasks():
    big = planned("A", hours=60, topics=[f"t{i}" for i in range(6)], exercises=["e"], project="p")
    assert len(build_roadmap([big], hours_per_week=2)) == 8

    tiny = planned("B", hours=60, topics=[], exercises=[], project="p")  # one task only
    assert len(build_roadmap([tiny], hours_per_week=2)) == 1


def test_every_task_appears_exactly_once_and_project_is_last():
    skill = planned("A", hours=24, topics=["t1", "t2", "t3"], exercises=["e1", "e2"], project="proj")
    weeks = build_roadmap([skill], hours_per_week=6)
    tasks = [task for week in weeks for task in week.tasks]

    assert len(tasks) == 6  # 3 topics + 2 exercises + 1 project
    assert [t.description for t in tasks] == [
        "Study: t1", "Study: t2", "Study: t3",
        "Practice: e1", "Practice: e2", "Build: proj",
    ]
    assert weeks[-1].tasks[-1].task_type == "project"


def test_skills_are_scheduled_one_after_another():
    skills = [
        planned("A", hours=8, topics=["t"], project="p"),
        planned("B", hours=8, topics=["t"], project="p"),
    ]
    weeks = build_roadmap(skills, hours_per_week=8)
    assert [w.skill for w in weeks] == ["A", "B"]


def test_skill_without_content_still_gets_a_task():
    weeks = build_roadmap([planned("A", hours=8)], hours_per_week=8)
    assert len(weeks) == 1
    assert weeks[0].tasks[0].description == "Study the fundamentals of A"


def test_task_hours_are_positive_and_add_up_to_the_estimate():
    skill = planned("A", hours=20, topics=["a", "b"], exercises=["c", "d"], project="p")
    tasks = [t for w in build_roadmap([skill], 10) for t in w.tasks]
    assert all(t.estimated_hours > 0 for t in tasks)
    assert round(sum(t.estimated_hours for t in tasks)) == 20


def test_roadmap_is_deterministic():
    skills = [planned("A", hours=18, topics=["a", "b", "c"], exercises=["d"], project="p")]
    assert build_roadmap(skills, 6) == build_roadmap(skills, 6)


def test_last_week_uses_expected_outcome_and_earlier_weeks_use_objectives():
    skill = planned("A", hours=20, topics=["a", "b", "c", "d"], project="p",
                    objectives=["objective one"])
    weeks = build_roadmap([skill], hours_per_week=10)
    assert weeks[0].expected_outcome == "objective one"
    assert weeks[-1].expected_outcome == "can do it"


# --------------------------------------------------------------------------
# Progress and candidate summary
# --------------------------------------------------------------------------

def test_progress_percentages():
    assert compute_progress(0, 0) == {"completed_tasks": 0, "total_tasks": 0, "percent": 0}
    assert compute_progress(1, 3)["percent"] == 33
    assert compute_progress(2, 3)["percent"] == 67
    assert compute_progress(4, 4)["percent"] == 100


def test_experience_summary_is_factual():
    summary = summarize_experience(
        [{"job_title": "Dev", "company": "Acme", "start_date": "Jan 2022", "end_date": "Jan 2024"}],
        today=date(2026, 11, 22),
    )
    assert "2.0 years" in summary and "Dev at Acme" in summary
    assert summarize_experience([]) == "No work experience listed on the resume."
