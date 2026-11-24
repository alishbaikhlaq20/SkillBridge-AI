"""
Shared test setup.

IMPORTANT: the environment variables below are set BEFORE the application is
imported. database.py reads DATABASE_URL at import time and python-dotenv never
overrides a variable that is already set, so these tests ALWAYS use a throwaway
SQLite file and can never touch the real PostgreSQL database from your .env.
"""

import os
import tempfile
from pathlib import Path

_TEST_DIR = Path(tempfile.mkdtemp(prefix="career_tests_"))

os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_DIR / 'test.db').as_posix()}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["GEMINI_API_KEY"] = "test-key-never-used"

import json  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from database import Base, SessionLocal, engine  # noqa: E402
from models import (  # noqa: E402
    JobAnalysis,
    MatchResult,
    Resume,
    ResumeExperience,
    ResumeSkill,
)

PASSWORD = "Passw0rd!x"


@pytest.fixture(autouse=True)
def clean_database():
    """Every test starts with empty tables."""

    # Safety guard: never drop tables of a real database.
    assert engine.url.drivername.startswith("sqlite"), (
        "Tests must run on SQLite, not on " + str(engine.url)
    )

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    return TestClient(main.app)


def register_and_login(client: TestClient, email: str) -> dict:
    response = client.post(
        "/register",
        json={"email": email, "password": PASSWORD, "full_name": "Test User"},
    )
    assert response.status_code == 200, response.text

    login = client.post("/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.text

    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture()
def user_a(client):
    return register_and_login(client, "a@example.com")


@pytest.fixture()
def user_b(client):
    return register_and_login(client, "b@example.com")


def seed_match(
    user_id: int = 1,
    resume_skills=("python", "sql"),
    required=("Python", "Docker", "Communication Skills", "Kubernetes"),
    preferred=("AWS",),
    missing=("Docker", "Communication Skills", "Kubernetes", "AWS"),
    job_title="Backend Developer",
) -> dict:
    """Create a resume, a job and a saved match for one user directly in the DB."""

    db = SessionLocal()

    try:
        resume = Resume(
            user_id=user_id, file_name="cv.pdf", file_path="x",
            file_type="application/pdf", file_size=1, extracted_text="text",
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        for skill in resume_skills:
            db.add(ResumeSkill(resume_id=resume.id, skill_name=skill))

        db.add(
            ResumeExperience(
                resume_id=resume.id, job_title="Junior Developer",
                company="Acme", start_date="Jan 2023", end_date="Jan 2024",
                description="Built APIs",
            )
        )

        job = JobAnalysis(
            user_id=user_id, description="d" * 60, job_title=job_title,
            company="Globex",
            required_skills=json.dumps(list(required)),
            preferred_skills=json.dumps(list(preferred)),
            education_requirements=json.dumps([]),
            experience_requirements=json.dumps([]),
            responsibilities=json.dumps(["Build REST APIs", "Deploy services"]),
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        match = MatchResult(
            user_id=user_id, resume_id=resume.id, job_id=job.id,
            overall_score=50, skills_score=50, experience_score=50,
            education_score=50,
            matching_skills=json.dumps(["Python"]),
            missing_skills=json.dumps(list(missing)),
        )
        db.add(match)
        db.commit()
        db.refresh(match)

        return {"match_id": match.id, "job_id": job.id, "resume_id": resume.id}

    finally:
        db.close()
