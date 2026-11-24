"""
Unit tests for the deterministic matching engine.

Run from the backend folder:

    python -m pytest -v
"""

from datetime import date

from services.matching import (
    calculate_education_score,
    calculate_experience_score,
    calculate_match,
    calculate_skills_score,
    estimate_years_of_experience,
    extract_required_years,
    normalize_skill,
    unique_skills,
)

TODAY = date(2026, 11, 22)


# --------------------------------------------------------------------------
# Skill normalization
# --------------------------------------------------------------------------

def test_common_synonyms_normalize_to_one_name():
    assert normalize_skill("React.js") == normalize_skill("ReactJS") == "react"
    assert normalize_skill("Next.js") == normalize_skill("NextJS") == "nextjs"
    assert normalize_skill("Node") == normalize_skill("Node.js") == "nodejs"
    assert normalize_skill("Postgres") == "postgresql"
    assert normalize_skill("REST APIs") == normalize_skill("RESTful API") == "rest api"
    assert normalize_skill("JS") == "javascript"


def test_skills_suffix_and_hyphens_are_ignored():
    assert normalize_skill("Communication Skills") == "communication"
    assert normalize_skill("Problem-Solving") == "problem solving"


def test_leading_dot_is_kept():
    assert normalize_skill(".NET") == ".net"


def test_unique_skills_keeps_first_spelling():
    assert unique_skills(["React", "React.js", "react", "  "]) == {"react": "React"}


# --------------------------------------------------------------------------
# Skills score  (these were real bugs before)
# --------------------------------------------------------------------------

def test_duplicate_job_skills_do_not_push_score_above_100():
    score, matching, missing = calculate_skills_score(
        resume_skills=["python", "react"],
        required_skills=["React", "React.js", "Python"],
        preferred_skills=[],
    )
    assert score == 100
    assert matching == ["React", "Python"]
    assert missing == []


def test_duplicate_spelling_cannot_hide_a_missing_skill():
    score, matching, missing = calculate_skills_score(
        resume_skills=["python"],
        required_skills=["Python", "python", "Docker"],
        preferred_skills=[],
    )
    assert score == 50
    assert missing == ["Docker"]


def test_synonyms_in_resume_count_as_matches():
    score, matching, missing = calculate_skills_score(
        resume_skills=["NextJS", "Postgres", "communication"],
        required_skills=["Next.js", "PostgreSQL", "Communication Skills"],
        preferred_skills=[],
    )
    assert score == 100
    assert missing == []


def test_skill_in_both_lists_counts_once_as_required():
    score, matching, missing = calculate_skills_score(
        resume_skills=[],
        required_skills=["Python"],
        preferred_skills=["python", "Docker"],
    )
    assert missing == ["Python", "Docker"]


def test_required_is_80_percent_and_preferred_20_percent():
    score, _, _ = calculate_skills_score(
        resume_skills=["python"],
        required_skills=["Python"],
        preferred_skills=["Docker"],
    )
    assert score == 80


def test_no_skills_listed_scores_zero():
    score, matching, missing = calculate_skills_score(["python"], [], [])
    assert (score, matching, missing) == (0, [], [])


def test_score_is_always_between_0_and_100():
    for resume in ([], ["a"], ["a", "b", "c"]):
        score, _, _ = calculate_skills_score(
            resume, ["A", "a", "B", "b", "C", "c", "c"], ["A", "D"]
        )
        assert 0 <= score <= 100


# --------------------------------------------------------------------------
# Required years parsing  (the "+" bug)
# --------------------------------------------------------------------------

def test_extract_required_years():
    assert extract_required_years(["2 years of experience"]) == 2
    assert extract_required_years(["2+ years of experience"]) == 2
    assert extract_required_years(["5+ years of backend work"]) == 5
    assert extract_required_years(["3-5 years"]) == 3
    assert extract_required_years(["2 to 4 years"]) == 2
    assert extract_required_years(["At least 5 years"]) == 5
    assert extract_required_years(["Minimum five years"]) == 5
    assert extract_required_years(["3 yrs"]) == 3


def test_extract_required_years_none_when_no_number():
    assert extract_required_years(["Experience with Django"]) is None
    assert extract_required_years([]) is None


def test_largest_minimum_is_used_when_several_mentioned():
    assert extract_required_years(["3 years Python", "5 years in software"]) == 5


# --------------------------------------------------------------------------
# Years of experience from dates
# --------------------------------------------------------------------------

def test_estimate_years_from_month_and_year():
    jobs = [{"start_date": "Jan 2020", "end_date": "Jan 2023"}]
    assert estimate_years_of_experience(jobs, TODAY) == 3.0


def test_present_uses_todays_date():
    jobs = [{"start_date": "Nov 2024", "end_date": "Present"}]
    assert estimate_years_of_experience(jobs, TODAY) == 2.0


def test_year_only_dates_count_whole_years():
    jobs = [{"start_date": "2019", "end_date": "2021"}]
    assert estimate_years_of_experience(jobs, TODAY) == 2.0


def test_overlapping_jobs_are_not_counted_twice():
    jobs = [
        {"start_date": "Jan 2020", "end_date": "Jan 2022"},
        {"start_date": "Jan 2021", "end_date": "Jan 2023"},
    ]
    assert estimate_years_of_experience(jobs, TODAY) == 3.0


def test_unreadable_dates_return_none():
    assert estimate_years_of_experience([{"start_date": None, "end_date": None}], TODAY) is None
    assert estimate_years_of_experience([{"start_date": "recently", "end_date": "later"}], TODAY) is None
    assert estimate_years_of_experience([], TODAY) is None


# --------------------------------------------------------------------------
# Experience score
# --------------------------------------------------------------------------

def test_no_requirement_gives_full_score():
    assert calculate_experience_score([], [], TODAY) == 100


def test_requirement_but_no_experience_gives_zero():
    assert calculate_experience_score([], ["2+ years"], TODAY) == 0


def test_requirement_without_years_gives_full_score_if_experienced():
    jobs = [{"start_date": "2020", "end_date": "2021"}]
    assert calculate_experience_score(jobs, ["Experience with Django"], TODAY) == 100


def test_score_compares_candidate_years_to_required_years():
    three_years = [{"start_date": "Jan 2020", "end_date": "Jan 2023"}]
    one_year = [{"start_date": "Jan 2022", "end_date": "Jan 2023"}]
    assert calculate_experience_score(three_years, ["2+ years"], TODAY) == 100
    assert calculate_experience_score(one_year, ["2+ years"], TODAY) == 50
    assert calculate_experience_score(one_year, ["4 years"], TODAY) == 25


def test_unreadable_dates_give_partial_credit():
    jobs = [{"job_title": "Dev", "start_date": None, "end_date": None}]
    assert calculate_experience_score(jobs, ["3 years"], TODAY) == 50


# --------------------------------------------------------------------------
# Education score (behaviour unchanged)
# --------------------------------------------------------------------------

def test_education_scores():
    cs = [{"degree": "BS Computer Science", "university": "X"}]
    assert calculate_education_score(cs, []) == 100
    assert calculate_education_score([], ["Computer Science degree"]) == 0
    assert calculate_education_score(cs, ["Computer Science degree"]) == 100
    assert calculate_education_score(cs, ["Bachelor's degree"]) == 80
    assert calculate_education_score([{"degree": "BA History"}], ["Bachelor's degree"]) == 50


# --------------------------------------------------------------------------
# Overall match
# --------------------------------------------------------------------------

def test_overall_uses_50_30_20_weights():
    result = calculate_match(
        resume_skills=["python"],
        resume_experience=[{"start_date": "Jan 2020", "end_date": "Jan 2023"}],
        resume_education=[{"degree": "BS Computer Science"}],
        required_skills=["Python", "Docker"],
        preferred_skills=[],
        experience_requirements=["2 years"],
        education_requirements=["Computer Science"],
    )
    # skills 50, experience 100, education 100  ->  25 + 30 + 20
    assert result.skills_score == 50
    assert result.experience_score == 100
    assert result.education_score == 100
    assert result.overall_score == 75


def test_calculation_is_deterministic():
    args = dict(
        resume_skills=["python", "react"],
        resume_experience=[],
        resume_education=[],
        required_skills=["Python", "Docker", "Kubernetes"],
        preferred_skills=["AWS"],
        experience_requirements=[],
        education_requirements=[],
    )
    assert calculate_match(**args) == calculate_match(**args)
