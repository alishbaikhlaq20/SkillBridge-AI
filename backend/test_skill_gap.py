"""
Unit tests for skill-gap classification and prioritisation.

Run from the backend folder:  python -m pytest -v
"""

from services.skill_gap import (
    classify_category,
    decide_priority,
    generate_skill_gaps,
)


# --------------------------------------------------------------------------
# Categories
# --------------------------------------------------------------------------

def test_technical_categories():
    assert classify_category("Python") == "Programming Language"
    assert classify_category("SQL") == "Programming Language"
    assert classify_category("FastAPI") == "Framework / Library"
    assert classify_category("PostgreSQL") == "Database"
    assert classify_category("Docker") == "Tool / Platform"
    assert classify_category("Microservices") == "Technical Concept"


def test_synonym_spellings_get_the_same_category():
    assert classify_category("React.js") == "Framework / Library"
    assert classify_category("ReactJS") == "Framework / Library"
    assert classify_category("Next.js") == "Framework / Library"
    assert classify_category("Node.js") == "Framework / Library"
    assert classify_category("Postgres") == "Database"
    assert classify_category("REST APIs") == "Technical Concept"
    assert classify_category("RESTful API") == "Technical Concept"
    assert classify_category("K8s") == "Tool / Platform"


def test_soft_skills_are_professional_not_technical():
    for skill in [
        "Communication",
        "Communication Skills",
        "Strong communication skills",
        "Team player",
        "Problem-Solving",
        "Leadership",
        "Time management",
        "Analytical thinking",
        "Attention to detail",
    ]:
        assert classify_category(skill) == "Professional Skill", skill


def test_software_development_is_technical_not_professional():
    assert classify_category("Software Development") == "Technical Concept"


def test_unknown_skill_defaults_to_technical_skill():
    assert classify_category("Blockchain") == "Technical Skill"


# --------------------------------------------------------------------------
# Priority
# --------------------------------------------------------------------------

def test_priority_rules():
    assert decide_priority("Database", is_required=True) == "High"
    assert decide_priority("Database", is_required=False) == "Medium"
    assert decide_priority("Professional Skill", is_required=True) == "Medium"
    assert decide_priority("Professional Skill", is_required=False) == "Medium"


def test_priority_depends_on_required_not_on_category():
    gaps = generate_skill_gaps(
        missing_skills=["Docker", "FastAPI"],
        required_skills=["Docker"],          # FastAPI is only preferred
    )
    by_skill = {gap.skill: gap for gap in gaps}

    # Docker is a "tool" (used to be Medium) but is required -> High
    assert by_skill["Docker"].priority == "High"
    # FastAPI is a "framework" (used to be High) but is only preferred -> Medium
    assert by_skill["FastAPI"].priority == "Medium"


def test_required_match_uses_normalized_names():
    gaps = generate_skill_gaps(
        missing_skills=["React.js"],
        required_skills=["ReactJS"],
    )
    assert gaps[0].priority == "High"


def test_required_soft_skill_is_medium_with_experience_advice():
    gap = generate_skill_gaps(
        missing_skills=["Communication Skills"],
        required_skills=["Communication Skills"],
    )[0]
    assert gap.category == "Professional Skill"
    assert gap.priority == "Medium"
    assert "experience" in gap.reason


def test_without_required_list_everything_is_medium():
    gaps = generate_skill_gaps(["Docker", "Python"])
    assert [gap.priority for gap in gaps] == ["Medium", "Medium"]


# --------------------------------------------------------------------------
# Reasons, duplicates, order
# --------------------------------------------------------------------------

def test_reason_says_required_or_preferred():
    gaps = generate_skill_gaps(
        missing_skills=["Docker", "AWS"],
        required_skills=["Docker"],
    )
    assert "required" in gaps[0].reason
    assert "preferred" in gaps[1].reason


def test_duplicate_missing_skills_become_one_gap():
    gaps = generate_skill_gaps(
        missing_skills=["React", "React.js", "react"],
        required_skills=["React"],
    )
    assert len(gaps) == 1
    assert gaps[0].skill == "React"


def test_original_order_and_spelling_are_kept():
    gaps = generate_skill_gaps(["Docker", "Python", "Kubernetes"])
    assert [gap.skill for gap in gaps] == ["Docker", "Python", "Kubernetes"]


def test_empty_input_gives_no_gaps():
    assert generate_skill_gaps([]) == []
