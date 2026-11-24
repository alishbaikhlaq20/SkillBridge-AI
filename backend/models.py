from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        nullable=False,
        unique=True
    )

    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    education = Column(String, nullable=True)
    university = Column(String, nullable=True)
    degree = Column(String, nullable=True)
    graduation_year = Column(Integer, nullable=True)
    experience_years = Column(Integer, nullable=True)
    bio = Column(String, nullable=True)

    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    file_name = Column(
        String,
        nullable=False
    )

    file_path = Column(
        String,
        nullable=False
    )

    file_type = Column(
        String,
        nullable=False
    )

    file_size = Column(
        Integer,
        nullable=False
    )

    extracted_text = Column(
        String,
        nullable=True
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
class ResumeSkill(Base):
    __tablename__ = "resume_skills"

    id = Column(Integer, primary_key=True, index=True)

    resume_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    skill_name = Column(
        String,
        nullable=False
    )
class ResumeEducation(Base):
    __tablename__ = "resume_education"

    id = Column(Integer, primary_key=True, index=True)

    resume_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    degree = Column(
        String,
        nullable=True
    )

    university = Column(
        String,
        nullable=True
    )

    location = Column(
        String,
        nullable=True
    )

    cgpa = Column(
        String,
        nullable=True
    )

    graduation_year = Column(
        Integer,
        nullable=True
    )
class ResumeExperience(Base):
    __tablename__ = "resume_experience"

    id = Column(Integer, primary_key=True, index=True)

    resume_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    job_title = Column(
        String,
        nullable=True
    )

    company = Column(
        String,
        nullable=True
    )

    start_date = Column(
        String,
        nullable=True
    )

    end_date = Column(
        String,
        nullable=True
    )

    description = Column(
        String,
        nullable=True
    )
class JobAnalysis(Base):
    __tablename__ = "job_analyses"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    job_title = Column(
        String,
        nullable=True
    )

    company = Column(
        String,
        nullable=True
    )

    description = Column(
        String,
        nullable=False
    )

    required_skills = Column(
        String,
        nullable=True
    )

    preferred_skills = Column(
        String,
        nullable=True
    )

    education_requirements = Column(
        String,
        nullable=True
    )

    experience_requirements = Column(
        String,
        nullable=True
    )

    responsibilities = Column(
        String,
        nullable=True
    )

    analyzed_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    resume_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    job_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    overall_score = Column(
        Integer,
        nullable=False
    )

    skills_score = Column(
        Integer,
        nullable=False
    )

    experience_score = Column(
        Integer,
        nullable=False
    )

    education_score = Column(
        Integer,
        nullable=False
    )

    matching_skills = Column(
        String,
        nullable=True
    )

    missing_skills = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Learning plans
#
# These tables use real foreign keys. Deleting a user, a match or a plan also
# removes the rows that depend on it, so no orphan rows are left behind.
# ---------------------------------------------------------------------------

class LearningPlan(Base):
    __tablename__ = "learning_plans"

    # One plan per user and match. This also stops a double click from
    # creating two plans.
    __table_args__ = (
        UniqueConstraint(
            "user_id", "match_id", name="uq_learning_plan_user_match"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    match_id = Column(
        Integer,
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_id = Column(
        Integer,
        ForeignKey("job_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String, nullable=False)
    overview = Column(Text, nullable=True)

    hours_per_week = Column(Integer, nullable=False)
    total_weeks = Column(Integer, nullable=False)
    total_hours = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    skills = relationship(
        "LearningPlanSkill",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="LearningPlanSkill.order_index",
    )

    weeks = relationship(
        "LearningPlanWeek",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="LearningPlanWeek.week_number",
    )


class LearningPlanSkill(Base):
    __tablename__ = "learning_plan_skills"

    id = Column(Integer, primary_key=True, index=True)

    plan_id = Column(
        Integer,
        ForeignKey("learning_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_index = Column(Integer, nullable=False)

    skill = Column(String, nullable=False)
    category = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)

    why_it_matters = Column(Text, nullable=True)
    starting_point = Column(Text, nullable=True)
    estimated_hours = Column(Integer, nullable=False)

    prerequisites = Column(JSON, nullable=False, default=list)
    learning_objectives = Column(JSON, nullable=False, default=list)
    beginner_topics = Column(JSON, nullable=False, default=list)
    intermediate_topics = Column(JSON, nullable=False, default=list)
    advanced_topics = Column(JSON, nullable=False, default=list)
    practical_exercises = Column(JSON, nullable=False, default=list)
    resources = Column(JSON, nullable=False, default=list)

    mini_project = Column(Text, nullable=True)
    expected_outcome = Column(Text, nullable=True)

    plan = relationship("LearningPlan", back_populates="skills")


class LearningPlanWeek(Base):
    __tablename__ = "learning_plan_weeks"

    id = Column(Integer, primary_key=True, index=True)

    plan_id = Column(
        Integer,
        ForeignKey("learning_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    week_number = Column(Integer, nullable=False)
    skill = Column(String, nullable=False)
    title = Column(String, nullable=False)
    expected_outcome = Column(Text, nullable=True)

    plan = relationship("LearningPlan", back_populates="weeks")

    tasks = relationship(
        "LearningPlanTask",
        back_populates="week",
        cascade="all, delete-orphan",
        order_by="LearningPlanTask.order_index",
    )


class LearningPlanTask(Base):
    __tablename__ = "learning_plan_tasks"

    id = Column(Integer, primary_key=True, index=True)

    # plan_id is stored on the task as well so that ownership checks and
    # progress counts need one simple query.
    plan_id = Column(
        Integer,
        ForeignKey("learning_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    week_id = Column(
        Integer,
        ForeignKey("learning_plan_weeks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_index = Column(Integer, nullable=False)

    skill = Column(String, nullable=False)
    task_type = Column(String, nullable=False)  # study | exercise | project
    description = Column(Text, nullable=False)
    estimated_hours = Column(Float, nullable=False)

    is_completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    week = relationship("LearningPlanWeek", back_populates="tasks")
class ResumeSkillAddition(Base):
    __tablename__ = "resume_skill_additions"

    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "skill",
            "evidence_level",
            name="uq_resume_skill_addition_plan_skill_level"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    plan_id = Column(
        Integer,
        ForeignKey("learning_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    skill = Column(String, nullable=False)

    # Learned, Practiced, or Demonstrated
    evidence_level = Column(String, nullable=False)

    # Editable resume wording
    suggestion_text = Column(Text, nullable=False)

    # IDs of the completed tasks supporting this suggestion
    source_task_ids = Column(JSON, nullable=False, default=list)

    is_selected = Column(Boolean, nullable=False, default=False)
    is_approved = Column(Boolean, nullable=False, default=False)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )