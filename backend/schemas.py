import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128
    )
    full_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if not re.search(r"[A-Z]", password):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )

        if not re.search(r"[a-z]", password):
            raise ValueError(
                "Password must contain at least one lowercase letter"
            )

        if not re.search(r"\d", password):
            raise ValueError(
                "Password must contain at least one number"
            )

        if not re.search(r"[^\w\s]", password):
            raise ValueError(
                "Password must contain at least one special character"
            )

        return password


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ProfileCreate(BaseModel):
    phone: str | None = None
    location: str | None = None
    education: str | None = None
    university: str | None = None
    degree: str | None = None
    graduation_year: int | None = None
    experience_years: int | None = None
    bio: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
class JobAnalysisCreate(BaseModel):
    description: str = Field(
        min_length=50,
        max_length=20000
    )


class LearningPlanRequest(BaseModel):
    match_id: int
    hours_per_week: int = Field(default=8, ge=2, le=40)
    regenerate: bool = False


class TaskUpdate(BaseModel):
    completed: bool
class ResumeSkillAdditionUpdate(BaseModel):
    suggestion_text: str = Field(
        min_length=1,
        max_length=1000
    )
    is_selected: bool


class ResumeSkillAdditionResponse(BaseModel):
    id: int
    skill: str
    evidence_level: str
    suggestion_text: str
    source_task_ids: list[int]
    is_selected: bool
    is_approved: bool

    class Config:
        from_attributes = True